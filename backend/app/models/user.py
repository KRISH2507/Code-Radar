import enum
from datetime import datetime, date

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Enum as SQLEnum
from sqlalchemy.sql import func

from app.core.database import Base


class Plan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class Role(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), unique=True, index=True, nullable=False)

    name = Column(String(255), nullable=True)

    hashed_password = Column(String(255), nullable=True)  # Nullable for Google OAuth users

    auth_provider = Column(String(50), default="email", nullable=False)  # "email" or "google"

    is_verified = Column(Boolean, default=False, nullable=False)

    # SaaS plan — stored as plain VARCHAR to avoid enum mismatch issues
    plan = Column(String(20), default="free", nullable=False)
    role = Column(String(20), default="user", nullable=False)
    scan_count = Column(Integer, default=0, nullable=False)
    scan_reset_date = Column(Date, default=date.today, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
