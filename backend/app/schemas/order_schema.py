"""
Schémas Commande
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus

class OrderCreate(BaseModel):
    product_id: int
    quantity: int = 1
    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_phone: Optional[str] = None
    delivery_notes: Optional[str] = None
    payment_method: str = "mobilepay"

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: Optional[str] = None

class DeliveryConfirmation(BaseModel):
    """Client confirme la livraison → déclenche paiement marchand"""
    order_id: int
    confirmation_code: str = Field(..., min_length=6, max_length=6)
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None

class OrderCancelRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)

class OrderResponse(BaseModel):
    id: int
    reference: str
    customer_id: int
    merchant_id: int
    product_id: int
    quantity: int
    total_amount: float
    delivery_fee: float
    status: OrderStatus
    customer_confirmed: bool
    delivery_address: Optional[str] = None
    tracking_code: Optional[str] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderDetailResponse(OrderResponse):
    platform_commission: float
    merchant_amount: float
    cancellation_reason: Optional[str] = None

class OrderTrackingResponse(BaseModel):
    order: OrderResponse
    timeline: list
    current_status: OrderStatus
    next_possible_actions: list