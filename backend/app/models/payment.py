"""
Modèles Paiement et Payout
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.config.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PayoutStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), unique=True, index=True, nullable=False)
    mobilepay_transaction_id = Column(String(100), unique=True, nullable=True)
    
    # Relations
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Payeur
    
    order = relationship("Order", back_populates="payments")
    user = relationship("User", foreign_keys=[user_id])
    
    # Montants
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="GNF")
    fees = Column(Float, default=0.0)  # Frais MobilePay
    
    # Statut
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Détails MobilePay
    payment_method = Column(String(50), default="mobilepay")
    payer_phone = Column(String(20), nullable=False)
    payer_name = Column(String(200), nullable=True)
    
    # Metadata
    metadata_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Payment {self.reference} - {self.amount} GNF - {self.status}>"

class Payout(Base):
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), unique=True, index=True, nullable=False)
    
    # Relations
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    # Montants
    amount = Column(Float, nullable=False)  # Montant net marchand
    commission_amount = Column(Float, nullable=False)  # Commission plateforme
    
    # Statut
    status = Column(Enum(PayoutStatus), default=PayoutStatus.PENDING)
    
    # Détails virement
    merchant_phone = Column(String(20), nullable=False)
    mobilepay_reference = Column(String(100), nullable=True)
    
    # Metadata
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Payout {self.reference} - {self.amount} GNF to merchant {self.merchant_id}>"