"""
Insight layer response schemas.

All fields are populated deterministically by InsightService —
no external AI call required; the output is structured for either
direct display or forwarding to an LLM as a pre-built prompt.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class SeverityBreakdown(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    info: int
    total: int


class TrendDelta(BaseModel):
    """Difference between current scan and the previous completed scan."""
    previous_scan_id: int
    health_score_delta: float   # positive = improved
    critical_delta: int
    high_delta: int
    medium_delta: int
    low_delta: int
    total_issues_delta: int
    direction: str              # "improved" | "regressed" | "stable"


class TopFile(BaseModel):
    file_path: str
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    complexity_score: Optional[float] = None
    language: Optional[str] = None


class RiskItem(BaseModel):
    """One identified risk category."""
    severity: str               # critical / high / medium
    category: str               # human-readable category name
    description: str            # what the risk means in practice
    rule_id: Optional[str]      # e.g. "CR002"
    affected_files: int
    occurrence_count: int


class RecommendedAction(BaseModel):
    priority: int               # 1 = highest
    action: str                 # short imperative
    rationale: str              # why this matters
    effort: str                 # low / medium / high
    impact: str                 # low / medium / high


class PriorityMatrixItem(BaseModel):
    """Two-axis effort × impact entry."""
    action: str
    effort: str
    impact: str
    priority_score: float       # higher = do first


# ---------------------------------------------------------------------------
# Top-level response
# ---------------------------------------------------------------------------

class InsightResponse(BaseModel):
    scan_id: int
    repository_id: int
    generated_at: datetime

    # Core metrics
    health_score: float
    severity_breakdown: SeverityBreakdown

    # Narrative
    executive_summary: str = Field(
        description="3-5 sentence plain-English summary of current code health."
    )
    technical_debt_estimate: str = Field(
        description="Estimated developer-hours / days to resolve all issues."
    )

    # Change tracking
    trend_delta: Optional[TrendDelta] = Field(
        None,
        description="Populated only when a previous completed scan exists.",
    )
    new_issues_count: int = Field(
        0, description="Issues present in current scan but not the previous."
    )
    resolved_issues_count: int = Field(
        0, description="Issues present in previous scan but not current."
    )

    # File-level intelligence
    top_problematic_files: List[TopFile]
    language_distribution: Dict[str, Any]   # {lang: {files, lines, pct}}

    # Action-oriented output
    risk_analysis: List[RiskItem]
    recommended_actions: List[RecommendedAction]
    priority_matrix: List[PriorityMatrixItem]
