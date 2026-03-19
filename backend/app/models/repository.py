from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class SourceType(str, enum.Enum):
    GITHUB = "github"
    ZIP = "zip"


class RepositoryStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    repo_url = Column(String(512), nullable=True)
    status = Column(
        SQLEnum(RepositoryStatus),
        default=RepositoryStatus.PENDING,
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scan metrics
    file_count = Column(Integer, nullable=True, default=0)
    line_count = Column(Integer, nullable=True, default=0)
    health_score = Column(Float, nullable=True)

    # Relationships
    scans = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="repository", cascade="all, delete-orphan")
    file_metrics = relationship("FileMetrics", cascade="all, delete-orphan")
