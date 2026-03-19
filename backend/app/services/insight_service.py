"""
InsightService
==============

Generates structured code-quality insights for a completed scan.
All analysis is deterministic (no external AI calls); the output is
suitable for direct display *or* as a pre-built context block for an LLM.

Design goals
------------
- Zero N+1 queries  — every aggregate uses a single GROUP BY or sub-query.
- Uses existing indexes — ix_issues_scan_severity, ix_file_metrics_scan_id,
  ix_scans_repository_id_created.
- No lazy-loading  — Scan.issues is lazy="dynamic" so we always use
  explicit queries.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from app.models.file_metrics import FileMetrics
from app.models.issue import Issue, IssueType, IssueSeverity
from app.models.repository import Repository
from app.models.scan import Scan, ScanStatus
from app.schemas.insight import (
    InsightResponse,
    PriorityMatrixItem,
    RecommendedAction,
    RiskItem,
    SeverityBreakdown,
    TopFile,
    TrendDelta,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minutes a developer typically spends fixing one issue of each severity.
_DEBT_MINUTES: Dict[str, float] = {
    "critical": 240.0,
    "high":     120.0,
    "medium":   60.0,
    "low":      15.0,
    "info":     5.0,
}

# Rule → (category name, short description, effort, impact)
_RULE_META: Dict[str, Tuple[str, str, str, str]] = {
    "CR001": (
        "File Size",
        "Oversized source files hurt readability and increase merge conflicts.",
        "medium", "medium",
    ),
    "CR002": (
        "Hardcoded Secrets",
        "Credentials or tokens stored in source code expose security vulnerabilities.",
        "low", "high",
    ),
    "CR003": (
        "Error Handling",
        "Empty catch blocks silently swallow exceptions, masking failures.",
        "low", "high",
    ),
    "CR004": (
        "Debug Code",
        "Console / print statements left in production bloat logs and may leak data.",
        "low", "medium",
    ),
    "CR005": (
        "Technical Debt Markers",
        "TODO / FIXME comments represent deferred work and accumulated debt.",
        "medium", "low",
    ),
    "CR006": (
        "Function Complexity",
        "Overly long functions are harder to test, review, and maintain.",
        "high", "high",
    ),
    "CR007": (
        "Deep Nesting",
        "Deeply nested control flow increases cognitive load and bug risk.",
        "medium", "high",
    ),
    "CR008": (
        "Cyclomatic Complexity",
        "High-complexity logic paths are difficult to test comprehensively.",
        "high", "high",
    ),
}

# Severity → numeric weight for risk ranking
_SEV_WEIGHT = {"critical": 40, "high": 20, "medium": 8, "low": 2, "info": 1}

# Effort / impact strings → numeric for priority score calculation
_EFFORT_NUM = {"low": 1, "medium": 2, "high": 3}
_IMPACT_NUM = {"low": 1, "medium": 2, "high": 3}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

class InsightService:

    @classmethod
    def generate(cls, scan: Scan, db: Session) -> InsightResponse:
        """
        Build a fully populated InsightResponse for a COMPLETED scan.
        Raises ValueError if the scan is not in COMPLETED status.
        """
        if scan.status != ScanStatus.COMPLETED:
            raise ValueError(
                f"Insights are only available for completed scans "
                f"(current status: {scan.status})"
            )

        repo_id = scan.repository_id

        # ── 1. Previous scan for delta ──────────────────────────────────────
        previous = (
            db.query(Scan)
            .filter(
                Scan.repository_id == repo_id,
                Scan.status == ScanStatus.COMPLETED,
                Scan.id != scan.id,
                Scan.created_at < scan.created_at,
            )
            .order_by(desc(Scan.created_at))
            .first()
        )

        # ── 2. Per-file issue counts (single GROUP BY, uses ix_issues_scan_severity)
        file_counts = cls._query_file_issue_counts(scan.id, db)

        # ── 3. File metrics (complexity + language) ─────────────────────────
        fm_map = cls._query_file_metrics(scan.id, db)

        # ── 4. Issue-type distribution ──────────────────────────────────────
        type_dist = cls._query_issue_type_distribution(scan.id, db)

        # ── 5. Build sub-sections ────────────────────────────────────────────
        severity_breakdown = cls._build_severity_breakdown(scan)
        trend_delta, new_count, resolved_count = cls._build_trend(
            scan, previous, db
        )
        top_files = cls._build_top_files(file_counts, fm_map)
        lang_dist = cls._build_language_distribution(scan)
        risk_analysis = cls._build_risk_analysis(type_dist, scan)
        recommended_actions = cls._build_recommended_actions(type_dist, scan)
        priority_matrix = cls._build_priority_matrix(recommended_actions)
        debt_str = cls._estimate_technical_debt(scan)
        summary = cls._build_executive_summary(scan, trend_delta, top_files)

        return InsightResponse(
            scan_id=scan.id,
            repository_id=repo_id,
            generated_at=datetime.now(timezone.utc),
            health_score=round(scan.health_score or 0.0, 1),
            severity_breakdown=severity_breakdown,
            executive_summary=summary,
            technical_debt_estimate=debt_str,
            trend_delta=trend_delta,
            new_issues_count=new_count,
            resolved_issues_count=resolved_count,
            top_problematic_files=top_files,
            language_distribution=lang_dist,
            risk_analysis=risk_analysis,
            recommended_actions=recommended_actions,
            priority_matrix=priority_matrix,
        )

    # -----------------------------------------------------------------------
    # DB queries
    # -----------------------------------------------------------------------

    @staticmethod
    def _query_file_issue_counts(
        scan_id: int, db: Session
    ) -> List[Dict[str, Any]]:
        """
        Return one row per file path with counts broken down by severity.
        Single query with conditional aggregation — no N+1.
        """
        rows = (
            db.query(
                Issue.file_path,
                func.count(Issue.id).label("total"),
                func.sum(
                    case((Issue.severity == IssueSeverity.CRITICAL, 1), else_=0)
                ).label("critical"),
                func.sum(
                    case((Issue.severity == IssueSeverity.HIGH, 1), else_=0)
                ).label("high"),
                func.sum(
                    case((Issue.severity == IssueSeverity.MEDIUM, 1), else_=0)
                ).label("medium"),
                func.sum(
                    case((Issue.severity == IssueSeverity.LOW, 1), else_=0)
                ).label("low"),
            )
            .filter(Issue.scan_id == scan_id)
            .group_by(Issue.file_path)
            .order_by(desc("total"))
            .limit(20)
            .all()
        )
        return [
            {
                "file_path": r.file_path,
                "total": int(r.total or 0),
                "critical": int(r.critical or 0),
                "high": int(r.high or 0),
                "medium": int(r.medium or 0),
                "low": int(r.low or 0),
            }
            for r in rows
        ]

    @staticmethod
    def _query_file_metrics(
        scan_id: int, db: Session
    ) -> Dict[str, Dict[str, Any]]:
        """Returns {file_path: {complexity_score, language}} — indexed query."""
        rows = (
            db.query(
                FileMetrics.file_path,
                FileMetrics.complexity_score,
                FileMetrics.language,
            )
            .filter(FileMetrics.scan_id == scan_id)
            .all()
        )
        return {
            r.file_path: {
                "complexity_score": r.complexity_score,
                "language": r.language,
            }
            for r in rows
        }

    @staticmethod
    def _query_issue_type_distribution(
        scan_id: int, db: Session
    ) -> List[Dict[str, Any]]:
        """
        Returns one row per (issue_type, dominant_severity) with counts and
        affected file count — single query, uses GROUP BY.
        """
        rows = (
            db.query(
                Issue.issue_type,
                Issue.severity,
                func.count(Issue.id).label("count"),
                func.count(func.distinct(Issue.file_path)).label("files"),
            )
            .filter(Issue.scan_id == scan_id)
            .group_by(Issue.issue_type, Issue.severity)
            .order_by(desc("count"))
            .all()
        )

        # Merge rows with same issue_type; keep worst severity
        merged: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            key = r.issue_type.value if hasattr(r.issue_type, "value") else str(r.issue_type)
            sev = r.severity.value if hasattr(r.severity, "value") else str(r.severity)
            if key not in merged:
                merged[key] = {
                    "issue_type": key,
                    "severity": sev,
                    "count": int(r.count or 0),
                    "files": int(r.files or 0),
                }
            else:
                merged[key]["count"] += int(r.count or 0)
                # Upgrade severity to worst seen
                if _SEV_WEIGHT.get(sev, 0) > _SEV_WEIGHT.get(merged[key]["severity"], 0):
                    merged[key]["severity"] = sev

        return sorted(
            merged.values(),
            key=lambda x: _SEV_WEIGHT.get(x["severity"], 0) * x["count"],
            reverse=True,
        )

    @staticmethod
    def _query_fingerprints(scan_id: int, db: Session) -> Set[Tuple[str, str, int]]:
        """Return a set of (issue_type, file_path, line_number) fingerprints."""
        rows = (
            db.query(Issue.issue_type, Issue.file_path, Issue.line_number)
            .filter(Issue.scan_id == scan_id)
            .all()
        )
        return {
            (
                r.issue_type.value if hasattr(r.issue_type, "value") else str(r.issue_type),
                r.file_path or "",
                r.line_number or 0,
            )
            for r in rows
        }

    # -----------------------------------------------------------------------
    # Section builders
    # -----------------------------------------------------------------------

    @staticmethod
    def _build_severity_breakdown(scan: Scan) -> SeverityBreakdown:
        c = int(scan.critical_count or 0)
        h = int(scan.high_count or 0)
        m = int(scan.medium_count or 0)
        l = int(scan.low_count or 0)
        i = int(scan.info_count or 0)
        return SeverityBreakdown(
            critical=c, high=h, medium=m, low=l, info=i,
            total=c + h + m + l + i
        )

    @classmethod
    def _build_trend(
        cls,
        current: Scan,
        previous: Optional[Scan],
        db: Session,
    ) -> Tuple[Optional[TrendDelta], int, int]:
        if previous is None:
            return None, 0, 0

        c_fps = cls._query_fingerprints(current.id, db)
        p_fps = cls._query_fingerprints(previous.id, db)
        new_count = len(c_fps - p_fps)
        resolved_count = len(p_fps - c_fps)

        cur_hs = current.health_score or 0.0
        pre_hs = previous.health_score or 0.0
        delta_hs = round(cur_hs - pre_hs, 1)

        cur_total = sum([
            current.critical_count or 0,
            current.high_count or 0,
            current.medium_count or 0,
            current.low_count or 0,
            current.info_count or 0,
        ])
        pre_total = sum([
            previous.critical_count or 0,
            previous.high_count or 0,
            previous.medium_count or 0,
            previous.low_count or 0,
            previous.info_count or 0,
        ])

        if delta_hs > 2:
            direction = "improved"
        elif delta_hs < -2:
            direction = "regressed"
        else:
            direction = "stable"

        return (
            TrendDelta(
                previous_scan_id=previous.id,
                health_score_delta=delta_hs,
                critical_delta=(current.critical_count or 0) - (previous.critical_count or 0),
                high_delta=(current.high_count or 0) - (previous.high_count or 0),
                medium_delta=(current.medium_count or 0) - (previous.medium_count or 0),
                low_delta=(current.low_count or 0) - (previous.low_count or 0),
                total_issues_delta=cur_total - pre_total,
                direction=direction,
            ),
            new_count,
            resolved_count,
        )

    @staticmethod
    def _build_top_files(
        file_counts: List[Dict[str, Any]],
        fm_map: Dict[str, Dict[str, Any]],
    ) -> List[TopFile]:
        result: List[TopFile] = []
        for fc in file_counts[:10]:
            fm = fm_map.get(fc["file_path"], {})
            result.append(
                TopFile(
                    file_path=fc["file_path"],
                    total_issues=fc["total"],
                    critical_count=fc["critical"],
                    high_count=fc["high"],
                    medium_count=fc["medium"],
                    complexity_score=fm.get("complexity_score"),
                    language=fm.get("language"),
                )
            )
        return result

    @staticmethod
    def _build_language_distribution(scan: Scan) -> Dict[str, Any]:
        raw: Dict[str, Any] = scan.language_stats or {}
        if not raw:
            return {}

        total_files = sum(v.get("files", 0) for v in raw.values())
        result: Dict[str, Any] = {}
        for lang, stats in raw.items():
            files = stats.get("files", 0)
            result[lang] = {
                "files": files,
                "lines": stats.get("lines", 0),
                "pct": round(files / total_files * 100, 1) if total_files else 0,
            }
        return result

    @staticmethod
    def _build_risk_analysis(
        type_dist: List[Dict[str, Any]], scan: Scan
    ) -> List[RiskItem]:
        # Map issue_type value → rule ID
        _RULE_FOR_TYPE = {
            "long_file":        "CR001",
            "hardcoded_secret": "CR002",
            "empty_catch":      "CR003",
            "debug_code":       "CR004",
            "todo_comment":     "CR005",
            "long_function":    "CR006",
            "deep_nesting":     "CR007",
            "high_complexity":  "CR008",
        }

        items: List[RiskItem] = []
        for row in type_dist:
            rule_id = _RULE_FOR_TYPE.get(row["issue_type"])
            meta = _RULE_META.get(rule_id, ("Unknown", "Unclassified issue type.", "medium", "medium")) if rule_id else ("Unknown", "Unclassified issue type.", "medium", "medium")
            sev = row["severity"]
            if sev in ("critical", "high", "medium"):
                items.append(
                    RiskItem(
                        severity=sev,
                        category=meta[0],
                        description=meta[1],
                        rule_id=rule_id,
                        affected_files=row["files"],
                        occurrence_count=row["count"],
                    )
                )
        return items[:8]  # cap at 8 risks

    @staticmethod
    def _build_recommended_actions(
        type_dist: List[Dict[str, Any]], scan: Scan
    ) -> List[RecommendedAction]:
        _ACTION_FOR_TYPE = {
            "hardcoded_secret": (
                "Remove hardcoded credentials from source code",
                "Secrets in source control are the #1 cause of credential leaks. "
                "Use environment variables or a secrets manager immediately.",
            ),
            "empty_catch": (
                "Add proper error handling to empty catch blocks",
                "Silent exception swallowing hides runtime failures and makes "
                "debugging significantly harder.",
            ),
            "high_complexity": (
                "Refactor high-complexity functions",
                "High cyclomatic complexity directly correlates with defect density "
                "and reduced test coverage.",
            ),
            "deep_nesting": (
                "Flatten deeply nested control flow using early returns",
                "Reducing nesting improves readability and lowers the chance of "
                "off-by-one / boundary errors.",
            ),
            "long_function": (
                "Break oversized functions into focused units",
                "Smaller functions are easier to test, review, and reuse.",
            ),
            "long_file": (
                "Split large files by responsibility",
                "Monolithic files increase merge conflicts and cognitive load.",
            ),
            "debug_code": (
                "Remove debug / console log statements",
                "Debug output in production pollutes logs and can expose internal "
                "state to attackers.",
            ),
            "todo_comment": (
                "Triage and schedule TODO / FIXME comments",
                "Convert informal debt markers into tracked issues so they are not "
                "forgotten.",
            ),
        }

        _RULE_FOR_TYPE = {
            "long_file":        "CR001",
            "hardcoded_secret": "CR002",
            "empty_catch":      "CR003",
            "debug_code":       "CR004",
            "todo_comment":     "CR005",
            "long_function":    "CR006",
            "deep_nesting":     "CR007",
            "high_complexity":  "CR008",
        }

        actions: List[RecommendedAction] = []
        for i, row in enumerate(type_dist[:8], start=1):
            itype = row["issue_type"]
            rule_id = _RULE_FOR_TYPE.get(itype)
            meta = _RULE_META.get(rule_id, ("Unknown", "", "medium", "medium")) if rule_id else ("Unknown", "", "medium", "medium")
            action_text, rationale = _ACTION_FOR_TYPE.get(
                itype, (f"Address {itype.replace('_', ' ')} issues", "Improves overall code quality.")
            )
            actions.append(
                RecommendedAction(
                    priority=i,
                    action=action_text,
                    rationale=rationale,
                    effort=meta[2],
                    impact=meta[3],
                )
            )
        return actions

    @staticmethod
    def _build_priority_matrix(
        actions: List[RecommendedAction],
    ) -> List[PriorityMatrixItem]:
        items: List[PriorityMatrixItem] = []
        for a in actions:
            effort_n = _EFFORT_NUM.get(a.effort, 2)
            impact_n = _IMPACT_NUM.get(a.impact, 2)
            # Priority = impact / effort  (higher = do first)
            score = round(impact_n / effort_n, 2)
            items.append(
                PriorityMatrixItem(
                    action=a.action,
                    effort=a.effort,
                    impact=a.impact,
                    priority_score=score,
                )
            )
        # Sort: highest priority_score first, then by impact desc
        items.sort(key=lambda x: (-x.priority_score, -_IMPACT_NUM.get(x.impact, 0)))
        return items

    @staticmethod
    def _estimate_technical_debt(scan: Scan) -> str:
        total_minutes = (
            (scan.critical_count or 0) * _DEBT_MINUTES["critical"]
            + (scan.high_count or 0) * _DEBT_MINUTES["high"]
            + (scan.medium_count or 0) * _DEBT_MINUTES["medium"]
            + (scan.low_count or 0) * _DEBT_MINUTES["low"]
            + (scan.info_count or 0) * _DEBT_MINUTES["info"]
        )
        hours = total_minutes / 60.0
        if hours < 1:
            return f"{int(total_minutes)} minutes"
        if hours < 8:
            return f"{hours:.1f} hours"
        days = hours / 8.0
        if days < 5:
            return f"{days:.1f} developer-days"
        weeks = days / 5.0
        return f"{weeks:.1f} developer-weeks"

    @staticmethod
    def _build_executive_summary(
        scan: Scan,
        trend: Optional[TrendDelta],
        top_files: List[TopFile],
    ) -> str:
        score = round(scan.health_score or 0.0, 1)
        critical = scan.critical_count or 0
        high = scan.high_count or 0
        total = sum([
            critical, high,
            scan.medium_count or 0,
            scan.low_count or 0,
            scan.info_count or 0,
        ])

        if score >= 80:
            health_label = "healthy"
        elif score >= 60:
            health_label = "moderate"
        elif score >= 40:
            health_label = "poor"
        else:
            health_label = "critical"

        lines: List[str] = []

        lines.append(
            f"This codebase has a health score of {score}/100 ({health_label}), "
            f"with {total} issue{'s' if total != 1 else ''} detected across "
            f"{scan.total_files or 0} file{'s' if (scan.total_files or 0) != 1 else ''}."
        )

        if critical > 0:
            lines.append(
                f"There {'are' if critical > 1 else 'is'} {critical} critical-severity "
                f"issue{'s' if critical != 1 else ''} that require immediate attention, "
                f"including potential hardcoded secrets or unhandled errors."
            )
        elif high > 0:
            lines.append(
                f"No critical issues were found, but {high} high-severity "
                f"issue{'s' if high != 1 else ''} (such as complex or deeply nested "
                f"functions) should be addressed in the near term."
            )
        else:
            lines.append(
                "No critical or high-severity issues were detected — "
                "the codebase is in good structural shape."
            )

        if trend:
            if trend.direction == "improved":
                lines.append(
                    f"Compared to the previous scan, health improved by "
                    f"{abs(trend.health_score_delta)} points "
                    f"with {trend.resolved_issues_count if hasattr(trend, 'resolved_issues_count') else 0} "
                    f"issues resolved."
                )
            elif trend.direction == "regressed":
                lines.append(
                    f"Health regressed by {abs(trend.health_score_delta)} points "
                    f"since the previous scan — {trend.total_issues_delta} new issues "
                    f"were introduced."
                )

        if top_files:
            worst = top_files[0]
            lines.append(
                f"The most problematic file is '{worst.file_path}' "
                f"with {worst.total_issues} issue{'s' if worst.total_issues != 1 else ''}."
            )

        return " ".join(lines)
