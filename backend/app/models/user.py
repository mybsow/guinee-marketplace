"""
Modèle Utilisateur (Clients et Marchands)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.config.database import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informations de base
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(200), nullable=False)
    
    # Rôle
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    
    # Vérification
    is_phone_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    is_kyc_verified = Column(Boolean, default=False)  # Pour les marchands
    kyc_documents = Column(String(500), nullable=True)  # URLs documents KYC
    
    # Informations personnelles (Guinée)
    national_id = Column(String(50), unique=True, nullable=True)  # N° CNI
    date_of_birth = Column(Date, nullable=True)
    address = Column(String(300), nullable=True)
    city = Column(String(100), default="Conakry")
    region = Column(String(100), nullable=True)
    
    # Marchand
    business_name = Column(String(200), nullable=True)
    business_description = Column(String(500), nullable=True)
    business_category = Column(String(100), nullable=True)
    
    # Réputation
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    
    # Solde (pour marchands)
    balance_gnf = Column(Float, default=0.0)  # Solde disponible
    pending_balance_gnf = Column(Float, default=0.0)  # En attente de libération
    
    # Préférences
    preferred_language = Column(String(10), default="fr")
    receive_sms_notifications = Column(Boolean, default=True)
    receive_email_notifications = Column(Boolean, default=False)
    
    # Statut
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    products = relationship("Product", back_populates="seller", lazy="dynamic")
    orders_as_customer = relationship("Order", foreign_keys="Order.customer_id", back_populates="customer", lazy="dynamic")
    orders_as_merchant = relationship("Order", foreign_keys="Order.merchant_id", back_populates="merchant", lazy="dynamic")
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.phone_number} ({self.role})>"
    
    @property
    def is_merchant(self):
        return self.role == UserRole.MERCHANT
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN