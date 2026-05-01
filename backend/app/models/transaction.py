"""
Modèle Transaction (pour comptabilité plateforme)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.sql import func
import enum
from app.config.database import Base

class TransactionType(str, enum.Enum):
    COMMISSION = "commission"
    PAYOUT = "payout"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    BONUS = "bonus"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), unique=True, index=True, nullable=False)
    
    # Type
    type = Column(Enum(TransactionType), nullable=False)
    
    # Montants
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="GNF")
    balance_before = Column(Float, default=0.0)
    balance_after = Column(Float, default=0.0)
    
    # Relations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Metadata
    metadata_json = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Transaction {self.reference} - {self.type} - {self.amount} GNF>"