"""
Payments API

POST /api/payments/create-order  – Create a Razorpay order
POST /api/payments/verify        – Verify payment and upgrade user to Pro
"""

import hashlib
import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import get_current_user
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, Plan
from app.schemas.payment import CreateOrderResponse, VerifyPaymentRequest, PaymentResponse

router = APIRouter()

# Pro plan price: ₹999/month  (99900 paise)
PRO_PLAN_AMOUNT = 99900
CURRENCY = "INR"


def _get_razorpay_client():
    """Lazily load razorpay client so the app boots even without the package."""
    try:
        import razorpay
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured on this server.",
        )

    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")

    if not key_id or not key_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway credentials are not configured.",
        )

    return razorpay.Client(auth=(key_id, key_secret)), key_id


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a Razorpay order for upgrading to Pro.
    Returns the order_id + Razorpay public key_id to the frontend.
    """
    if current_user.plan == Plan.PRO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already on the Pro plan.",
        )

    client, key_id = _get_razorpay_client()

    order_data = {
        "amount": PRO_PLAN_AMOUNT,
        "currency": CURRENCY,
        "payment_capture": 1,  # auto-capture
        "notes": {
            "user_id": str(current_user.id),
            "user_email": current_user.email,
        },
    }

    try:
        order = client.order.create(data=order_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create payment order: {str(e)}",
        )

    # Persist the pending order
    payment = Payment(
        user_id=current_user.id,
        razorpay_order_id=order["id"],
        amount=PRO_PLAN_AMOUNT,
        currency=CURRENCY,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()

    return CreateOrderResponse(
        order_id=order["id"],
        amount=PRO_PLAN_AMOUNT,
        currency=CURRENCY,
        key_id=key_id,
    )


@router.post("/verify", response_model=PaymentResponse)
def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verifies Razorpay payment signature.
    On success: marks the payment captured and upgrades user to Pro.
    """
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not key_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway credentials are not configured.",
        )

    # 1. Verify HMAC signature
    expected_sig = hmac.new(
        key_secret.encode("utf-8"),
        f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, payload.razorpay_signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed. Payment not recorded.",
        )

    # 2. Find the pending payment record
    payment = (
        db.query(Payment)
        .filter(
            Payment.razorpay_order_id == payload.razorpay_order_id,
            Payment.user_id == current_user.id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found.",
        )

    if payment.status == PaymentStatus.CAPTURED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This payment has already been processed.",
        )

    # 3. Update payment record
    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.razorpay_signature = payload.razorpay_signature
    payment.status = PaymentStatus.CAPTURED

    # 4. Upgrade user plan
    current_user.plan = Plan.PRO
    db.commit()
    db.refresh(payment)

    return payment
