"""
Analysis API Routes

GET  /api/analysis/repositories/{id}/status        – poll repo + latest scan
GET  /api/analysis/repositories/{id}/scans         – paginated scan history
GET  /api/analysis/scans/{scan_id}                 – single scan detail
GET  /api/analysis/scans/{scan_id}/issues          – paginated issues for a scan
GET  /api/analysis/repositories/{id}/trend         – health score trend data
GET  /api/analysis/repositories/{id}/scans/compare – diff two scans
POST /api/analysis/scans/{scan_id}/insights        – AI insight layer
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import get_current_user
from app.models.issue import Issue
from app.models.repository import Repository
from app.models.scan import Scan, ScanStatus
from app.models.user import User
from app.schemas.scan import (
    IssueListResponse,
    IssueResponse,
    RepositoryStatusResponse,
    ScanListResponse,
    ScanResponse,
    TrendPoint,
    TrendResponse,
)
from app.schemas.insight import InsightResponse
from app.services.insight_service import InsightService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_owned_repo(repo_id: int, user: User, db: Session) -> Repository:
    repo = (
        db.query(Repository)
        .filter(Repository.id == repo_id, Repository.user_id == user.id)
        .first()
    )
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Repository not found")
    return repo


def _get_owned_scan(scan_id: int, user: User, db: Session) -> Scan:
    scan = (
        db.query(Scan)
        .join(Repository, Scan.repository_id == Repository.id)
        .filter(Scan.id == scan_id, Repository.user_id == user.id)
        .first()
    )
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Scan not found")
    return scan


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/repositories/{repository_id}/status",
    response_model=RepositoryStatusResponse,
    summary="Poll repository scan status",
)
def get_repository_status(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the repository status together with the latest scan record.
    Poll this endpoint until ``latest_scan.status`` is ``completed`` or ``failed``.
    """
    repo = _get_owned_repo(repository_id, current_user, db)

    latest_scan = (
        db.query(Scan)
        .filter(Scan.repository_id == repository_id)
        .order_by(desc(Scan.created_at))
        .first()
    )

    return RepositoryStatusResponse(
        repository_id=repo.id,
        repository_status=repo.status.value,
        latest_scan=ScanResponse.model_validate(latest_scan) if latest_scan else None,
    )


@router.get(
    "/repositories/{repository_id}/scans",
    response_model=ScanListResponse,
    summary="Paginated scan history for a repository",
)
def list_repository_scans(
    repository_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all scans for a repository, newest first.
    Supports pagination via ``page`` and ``page_size`` query params.
    """
    _get_owned_repo(repository_id, current_user, db)

    base_q = db.query(Scan).filter(Scan.repository_id == repository_id)
    total  = base_q.count()

    scans = (
        base_q
        .order_by(desc(Scan.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ScanListResponse(scans=scans, total=total)


@router.get(
    "/scans/{scan_id}",
    response_model=ScanResponse,
    summary="Get single scan detail",
)
def get_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_scan(scan_id, current_user, db)


@router.get(
    "/scans/{scan_id}/issues",
    response_model=IssueListResponse,
    summary="Paginated issues for a scan",
)
def list_scan_issues(
    scan_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None, description="Filter by severity (critical/high/medium/low/info)"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns issues for a specific scan with optional severity/type filters.

    Ordered by severity (critical first) then file path.
    Uses a covering index on (scan_id, severity) – no N+1.
    """
    scan = _get_owned_scan(scan_id, current_user, db)

    # Severity ordering map for SQL CASE
    _SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

    base_q = db.query(Issue).filter(Issue.scan_id == scan.id)

    if severity:
        base_q = base_q.filter(Issue.severity == severity)
    if issue_type:
        base_q = base_q.filter(Issue.issue_type == issue_type)

    total = base_q.count()
    total_pages = math.ceil(total / page_size) if total else 1

    from sqlalchemy import case
    sev_order = case(
        (Issue.severity == "critical", 0),
        (Issue.severity == "high",     1),
        (Issue.severity == "medium",   2),
        (Issue.severity == "low",      3),
        (Issue.severity == "info",     4),
        else_=99,
    )

    issues = (
        base_q
        .order_by(sev_order, Issue.file_path, Issue.line_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return IssueListResponse(
        issues=issues,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/repositories/{repository_id}/trend",
    response_model=TrendResponse,
    summary="Health score trend (for charts)",
)
def get_health_trend(
    repository_id: int,
    limit: int = Query(30, ge=1, le=100, description="Number of most recent scans to include"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the last *N* completed scans with health score + critical/high counts.
    Designed for the dashboard trend chart.  Only COMPLETED scans are included.
    """
    _get_owned_repo(repository_id, current_user, db)

    scans = (
        db.query(Scan)
        .filter(
            Scan.repository_id == repository_id,
            Scan.status == ScanStatus.COMPLETED,
        )
        .order_by(desc(Scan.created_at))
        .limit(limit)
        .all()
    )

    # Return chronological order (oldest → newest) for charts
    scans = list(reversed(scans))

    return TrendResponse(
        repository_id=repository_id,
        data=[
            TrendPoint(
                scan_id=s.id,
                health_score=s.health_score,
                created_at=s.created_at,
                critical_count=s.critical_count,
                high_count=s.high_count,
            )
            for s in scans
        ],
    )


@router.get(
    "/repositories/{repository_id}/scans/compare",
    summary="Compare two scans (diff)",
)
def compare_scans(
    repository_id: int,
    scan_a: int = Query(..., description="Older scan ID"),
    scan_b: int = Query(..., description="Newer scan ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a diff summary between two scans of the same repository.
    Useful for showing improvement / regression after a re-scan.
    """
    _get_owned_repo(repository_id, current_user, db)

    a = _get_owned_scan(scan_a, current_user, db)
    b = _get_owned_scan(scan_b, current_user, db)

    if a.repository_id != repository_id or b.repository_id != repository_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Both scans must belong to the specified repository")

    # Count critical issues for both scans in a single query per scan
    def _issue_counts(scan: Scan):
        return {
            "total":    scan.critical_count + scan.high_count + scan.medium_count + scan.low_count + scan.info_count,
            "critical": scan.critical_count,
            "high":     scan.high_count,
            "medium":   scan.medium_count,
            "low":      scan.low_count,
            "info":     scan.info_count,
        }

    counts_a = _issue_counts(a)
    counts_b = _issue_counts(b)

    def _delta(key: str) -> int:
        return counts_b[key] - counts_a[key]

    return {
        "repository_id": repository_id,
        "scan_a": {"id": a.id, "created_at": a.created_at, "health_score": a.health_score, **counts_a},
        "scan_b": {"id": b.id, "created_at": b.created_at, "health_score": b.health_score, **counts_b},
        "delta": {
            "health_score": round((b.health_score or 0) - (a.health_score or 0), 2),
            "total_issues": _delta("total"),
            "critical":     _delta("critical"),
            "high":         _delta("high"),
            "medium":       _delta("medium"),
            "low":          _delta("low"),
            "info":         _delta("info"),
            "total_files":  (b.total_files or 0) - (a.total_files or 0),
            "total_lines":  (b.total_lines or 0) - (a.total_lines or 0),
        },
        "improved": (b.health_score or 0) >= (a.health_score or 0),
    }


# ---------------------------------------------------------------------------
# Insight layer
# ---------------------------------------------------------------------------

@router.post(
    "/scans/{scan_id}/insights",
    response_model=InsightResponse,
    summary="Generate AI-style insights for a completed scan",
    description=(
        "Returns a structured insight report including executive summary, "
        "risk analysis, recommended actions, technical debt estimate, and "
        "priority matrix. The scan must be in COMPLETED status."
    ),
)
def generate_scan_insights(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InsightResponse:
    scan = _get_owned_scan(scan_id, current_user, db)

    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Insights require a completed scan. "
                f"Current status: {scan.status.value if hasattr(scan.status, 'value') else scan.status}"
            ),
        )

    try:
        return InsightService.generate(scan, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
