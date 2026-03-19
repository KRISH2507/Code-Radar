from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

class ScanResponse(BaseModel):
    id: int
    repository_id: int
    status: str
    health_score: Optional[float] = None
    total_files: Optional[int] = None
    total_lines: Optional[int] = None
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    language_stats: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    scans: List[ScanResponse]
    total: int


# ---------------------------------------------------------------------------
# Issue
# ---------------------------------------------------------------------------

class IssueResponse(BaseModel):
    id: int
    scan_id: int
    repository_id: int
    severity: str
    issue_type: str
    file_path: str
    line_number: Optional[int] = None
    message: str
    rule: Optional[str] = None

    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    issues: List[IssueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Repository status (polling response)
# ---------------------------------------------------------------------------

class RepositoryStatusResponse(BaseModel):
    repository_id: int
    repository_status: str
    latest_scan: Optional[ScanResponse] = None


# ---------------------------------------------------------------------------
# Trend data (health score over time)
# ---------------------------------------------------------------------------

class TrendPoint(BaseModel):
    scan_id: int
    health_score: Optional[float]
    created_at: datetime
    critical_count: int
    high_count: int


class TrendResponse(BaseModel):
    repository_id: int
    data: List[TrendPoint]
