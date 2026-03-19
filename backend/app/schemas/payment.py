from pydantic import BaseModel
from typing import Optional


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int          # in paise
    currency: str
    key_id: str          # Razorpay public key (safe to expose to frontend)


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: int
    currency: str
    status: str

    class Config:
        from_attributes = True
