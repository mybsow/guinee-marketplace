"""
Modèle Commande
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.config.database import Base

class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"      # En attente de paiement
    PAYMENT_RECEIVED = "payment_received"    # Paiement reçu (séquestre)
    PAYMENT_FAILED = "payment_failed"        # Échec paiement
    PROCESSING = "processing"                # En préparation
    SHIPPED = "shipped"                      # Expédié
    DELIVERED = "delivered"                  # Livré (non confirmé)
    COMPLETED = "completed"                  # Confirmé par client → libération fonds
    CANCELLED = "cancelled"                  # Annulé
    REFUNDED = "refunded"                    # Remboursé
    DISPUTED = "disputed"                    # Litige

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), unique=True, index=True, nullable=False)
    
    # Relations
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    merchant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    customer = relationship("User", foreign_keys=[customer_id], back_populates="orders_as_customer")
    merchant = relationship("User", foreign_keys=[merchant_id], back_populates="orders_as_merchant")
    product = relationship("Product", back_populates="orders")
    
    # Détails commande
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Frais
    delivery_fee = Column(Float, default=0.0)
    platform_commission = Column(Float, default=0.0)
    merchant_amount = Column(Float, default=0.0)  # Montant net pour le marchand
    
    # Statut
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING_PAYMENT)
    
    # Informations livraison
    delivery_address = Column(Text, nullable=True)
    delivery_city = Column(String(100), nullable=True)
    delivery_phone = Column(String(20), nullable=True)
    delivery_notes = Column(Text, nullable=True)
    tracking_code = Column(String(100), nullable=True)
    
    # Confirmation
    customer_confirmed = Column(Boolean, default=False)  # Client confirme réception
    customer_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    merchant_confirmed = Column(Boolean, default=False)  # Marchand confirme envoi
    
    # Dates importantes
    paid_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Raison annulation
    cancellation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations paiement
    payments = relationship("Payment", back_populates="order")
    
    def __repr__(self):
        return f"<Order {self.reference} - {self.status}>"
    
    @property
    def can_be_cancelled(self):
        return self.status in [OrderStatus.PENDING_PAYMENT, OrderStatus.PAYMENT_RECEIVED]
    
    @property
    def is_completed(self):
        return self.status == OrderStatus.COMPLETED