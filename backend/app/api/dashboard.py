from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Any, Dict

from app.core.database import get_db
from app.core.jwt import get_current_user
from app.models.user import User
from app.models.repository import Repository, RepositoryStatus
from app.models.scan import Scan, ScanStatus

router = APIRouter()


# ---------------------------------------------------------------------------
# Safe coercion helpers — these are the single source of truth for
# "null → 0" normalization so NaN never reaches the frontend.
# ---------------------------------------------------------------------------

def _safe_int(value: Any, fallback: int = 0) -> int:
    """Return int(value) or fallback if value is None / non-numeric."""
    try:
        return int(value) if value is not None else fallback
    except (TypeError, ValueError):
        return fallback


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    """Return float(value) or fallback if value is None / non-numeric."""
    try:
        v = float(value) if value is not None else fallback
        return v if v == v else fallback   # reject NaN (NaN != NaN)
    except (TypeError, ValueError):
        return fallback


def _round(value: Any, ndigits: int = 1) -> float:
    return round(_safe_float(value), ndigits)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Aggregate stats for the current user.
    All issue counts and health score come from the latest completed
    Scan per repository — Repository.health_score is never used here
    because it can be stale on existing rows migrated before the worker
    was updated to write it.
    Guarantees: every numeric field is an int or float — never None or NaN.
    """
    # ── Repository counts ──────────────────────────────────────────────────
    total_repos    = _safe_int(db.query(func.count(Repository.id))
                               .filter(Repository.user_id == current_user.id)
                               .scalar())

    completed_repos = _safe_int(db.query(func.count(Repository.id))
                                 .filter(Repository.user_id == current_user.id,
                                         Repository.status == RepositoryStatus.COMPLETED)
                                 .scalar())

    scanning_repos  = _safe_int(db.query(func.count(Repository.id))
                                 .filter(Repository.user_id == current_user.id,
                                         Repository.status.in_([
                                             RepositoryStatus.PENDING,
                                             RepositoryStatus.PROCESSING,
                                         ]))
                                 .scalar())

    failed_repos    = _safe_int(db.query(func.count(Repository.id))
                                 .filter(Repository.user_id == current_user.id,
                                         Repository.status == RepositoryStatus.FAILED)
                                 .scalar())

    # ── File / line totals (from Repository rows written by the worker) ────
    agg = (
        db.query(
            func.sum(Repository.file_count).label("total_files"),
            func.sum(Repository.line_count).label("total_lines"),
        )
        .filter(Repository.user_id == current_user.id,
                Repository.status == RepositoryStatus.COMPLETED)
        .first()
    )
    total_files = _safe_int(agg.total_files if agg else None)
    total_lines = _safe_int(agg.total_lines if agg else None)

    # ── Health + issue counts from latest Scan per repo ────────────────────
    # Subquery: one row per repo → the highest scan id that is COMPLETED
    latest_subq = (
        db.query(
            Scan.repository_id,
            func.max(Scan.id).label("latest_scan_id"),
        )
        .join(Repository, Scan.repository_id == Repository.id)
        .filter(
            Repository.user_id == current_user.id,
            Scan.status == ScanStatus.COMPLETED,
        )
        .group_by(Scan.repository_id)
        .subquery()
    )

    scan_agg = (
        db.query(
            func.avg(Scan.health_score).label("avg_health_score"),
            func.sum(Scan.critical_count).label("total_critical"),
            func.sum(Scan.high_count).label("total_high"),
            func.sum(Scan.medium_count).label("total_medium"),
            func.sum(Scan.low_count).label("total_low"),
            func.sum(Scan.info_count).label("total_info"),
        )
        .join(latest_subq, Scan.id == latest_subq.c.latest_scan_id)
        .first()
    )

    # .first() on an aggregate with no rows returns a Row of all NULLs —
    # _safe_int / _safe_float handle that correctly.
    avg_health_score = _round(scan_agg.avg_health_score if scan_agg else None)
    total_critical   = _safe_int(scan_agg.total_critical  if scan_agg else None)
    total_high       = _safe_int(scan_agg.total_high       if scan_agg else None)
    total_medium     = _safe_int(scan_agg.total_medium     if scan_agg else None)
    total_low        = _safe_int(scan_agg.total_low        if scan_agg else None)
    total_info       = _safe_int(scan_agg.total_info       if scan_agg else None)

    return {
        "total_repositories": total_repos,
        "completed_scans":    completed_repos,
        "scanning_repos":     scanning_repos,
        "failed_scans":       failed_repos,
        "total_files":        total_files,
        "total_lines":        total_lines,
        "avg_health_score":   avg_health_score,
        "total_critical":     total_critical,
        "total_high":         total_high,
        "total_medium":       total_medium,
        "total_low":          total_low,
        "total_info":         total_info,
        "total_issues":       total_critical + total_high + total_medium + total_low + total_info,
    }


@router.get("/overview")
def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Recent repositories enriched with their latest completed scan data.
    Every numeric field is guaranteed non-null and non-NaN.
    """
    repos = (
        db.query(Repository)
        .filter(Repository.user_id == current_user.id)
        .order_by(Repository.created_at.desc())
        .limit(10)
        .all()
    )

    # Fetch latest completed scan per repo in one query
    repo_ids = [r.id for r in repos]
    latest_scans: Dict[int, Scan] = {}
    if repo_ids:
        subq = (
            db.query(
                Scan.repository_id,
                func.max(Scan.id).label("latest_id"),
            )
            .filter(
                Scan.repository_id.in_(repo_ids),
                Scan.status == ScanStatus.COMPLETED,
            )
            .group_by(Scan.repository_id)
            .subquery()
        )
        scans = db.query(Scan).join(subq, Scan.id == subq.c.latest_id).all()
        latest_scans = {s.repository_id: s for s in scans}

    def _repo_entry(repo: Repository) -> Dict[str, Any]:
        scan = latest_scans.get(repo.id)
        # health_score: prefer the Scan row (always fresh); fall back to the
        # denormalized Repository column for repos scanned before the last
        # migration, then to 0.
        health_score = _round(
            scan.health_score if scan else repo.health_score
        )
        return {
            "id":             repo.id,
            "name":           repo.name,
            "status":         repo.status.value,
            "source_type":    repo.source_type.value,
            "file_count":     _safe_int(repo.file_count),
            "line_count":     _safe_int(repo.line_count),
            "health_score":   health_score,
            "critical_count": _safe_int(scan.critical_count if scan else None),
            "high_count":     _safe_int(scan.high_count     if scan else None),
            "medium_count":   _safe_int(scan.medium_count   if scan else None),
            "low_count":      _safe_int(scan.low_count      if scan else None),
            "info_count":     _safe_int(scan.info_count     if scan else None),
            "total_issues":   _safe_int(
                (scan.critical_count or 0) + (scan.high_count or 0) +
                (scan.medium_count or 0) + (scan.low_count or 0) +
                (scan.info_count or 0)
                if scan else 0
            ),
            "latest_scan_id": scan.id if scan else None,
            "created_at":     repo.created_at.isoformat() if repo.created_at else None,
            "completed_at":   repo.completed_at.isoformat() if repo.completed_at else None,
        }

    return {
        "recent_repositories": [_repo_entry(r) for r in repos]
    }
