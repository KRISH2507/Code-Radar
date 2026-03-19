import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    razorpay_order_id = Column(String(255), nullable=False, unique=True, index=True)
    razorpay_payment_id = Column(String(255), nullable=True)
    razorpay_signature = Column(String(512), nullable=True)

    amount = Column(Integer, nullable=False)        # in paise (INR smallest unit)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    user = relationship("User", backref="payments")
