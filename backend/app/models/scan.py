from datetime import datetime
from sqlalchemy import (
    Column, DateTime, Float, Index, Integer, String,
    ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = (
        Index("ix_scans_repository_id_created", "repository_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    # Lifecycle
    status = Column(
        SQLEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False, index=True
    )
    task_id = Column(String(255), nullable=True)        # Celery task id
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Aggregate metrics (populated on completion)
    total_files = Column(Integer, nullable=True, default=0)
    total_lines = Column(Integer, nullable=True, default=0)
    health_score = Column(Float, nullable=True)          # 0 – 100
    language_stats = Column(JSONB, nullable=True)        # {lang: {files, lines}}

    # Issue counts per severity (denormalised for fast queries)
    critical_count = Column(Integer, nullable=False, default=0)
    high_count = Column(Integer, nullable=False, default=0)
    medium_count = Column(Integer, nullable=False, default=0)
    low_count = Column(Integer, nullable=False, default=0)
    info_count = Column(Integer, nullable=False, default=0)

    # Relationships
    repository = relationship("Repository", back_populates="scans")
    issues = relationship(
        "Issue", back_populates="scan", cascade="all, delete-orphan", lazy="dynamic"
    )
    file_metrics = relationship(
        "FileMetrics", back_populates="scan", cascade="all, delete-orphan"
    )
