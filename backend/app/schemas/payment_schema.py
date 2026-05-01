"""
Schémas Paiement
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.payment import PaymentStatus, PayoutStatus

class PaymentInitiate(BaseModel):
    order_id: int
    phone_number: str
    payment_method: str = "mobilepay"

class PaymentVerify(BaseModel):
    payment_reference: str
    transaction_id: str

class MobilePayWebhook(BaseModel):
    event: str  # payment.success, payment.failed, payout.completed
    transaction_id: str
    reference: str
    amount: float
    currency: str = "GNF"
    status: str
    metadata: Optional[dict] = None
    timestamp: datetime

class PaymentResponse(BaseModel):
    id: int
    reference: str
    order_id: int
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: str
    payer_phone: str
    mobilepay_transaction_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PayoutResponse(BaseModel):
    id: int
    reference: str
    order_id: int
    merchant_id: int
    amount: float
    commission_amount: float
    status: PayoutStatus
    merchant_phone: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TransactionHistory(BaseModel):
    payments: list
    payouts: list
    total_spent: float
    total_earned: float
    total_commission: float