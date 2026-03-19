from sqlalchemy import Column, Index, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(str, enum.Enum):
    LONG_FILE = "long_file"
    LONG_FUNCTION = "long_function"
    TODO_COMMENT = "todo_comment"
    DEBUG_CODE = "debug_code"
    EMPTY_CATCH = "empty_catch"
    HARDCODED_SECRET = "hardcoded_secret"
    DEEP_NESTING = "deep_nesting"
    HIGH_COMPLEXITY = "high_complexity"


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_scan_severity", "scan_id", "severity"),
        Index("ix_issues_repository_id", "repository_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(
        Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    repository_id = Column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    severity = Column(SQLEnum(IssueSeverity), nullable=False, index=True)
    issue_type = Column(SQLEnum(IssueType), nullable=False)
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, nullable=True)
    message = Column(String(1000), nullable=False)
    rule = Column(String(100), nullable=True)

    # Relationships
    scan = relationship("Scan", back_populates="issues")
    repository = relationship("Repository", back_populates="issues")
