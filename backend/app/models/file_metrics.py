from sqlalchemy import Column, Index, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class FileMetrics(Base):
    __tablename__ = "file_metrics"
    __table_args__ = (
        Index("ix_file_metrics_scan_id", "scan_id"),
    )

    id = Column(Integer, primary_key=True)
    scan_id = Column(
        Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    repository_id = Column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    file_path = Column(String(512), nullable=False)
    language = Column(String(50), nullable=True)
    total_lines = Column(Integer, default=0)
    code_lines = Column(Integer, default=0)
    blank_lines = Column(Integer, default=0)
    comment_lines = Column(Integer, default=0)
    complexity_score = Column(Float, nullable=True)   # simple nesting-depth proxy

    scan = relationship("Scan", back_populates="file_metrics")
