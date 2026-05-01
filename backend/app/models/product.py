"""
Modèle Produit/Annonce
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.config.database import Base

class ProductCategory(str, enum.Enum):
    ELECTRONICS = "electronics"
    VEHICLES = "vehicles"
    REAL_ESTATE = "real_estate"
    FASHION = "fashion"
    HOME_GARDEN = "home_garden"
    SPORTS = "sports"
    FOOD = "food"
    SERVICES = "services"
    JOBS = "jobs"
    ANIMALS = "animals"
    OTHER = "other"

class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    RESERVED = "reserved"
    INACTIVE = "inactive"
    REJECTED = "rejected"

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Informations de base
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="GNF")
    is_negotiable = Column(Boolean, default=True)
    
    # Catégorisation
    category = Column(Enum(ProductCategory), nullable=False)
    subcategory = Column(String(100), nullable=True)
    condition = Column(String(50), default="used")  # new, used, refurbished
    
    # Localisation (Guinée)
    city = Column(String(100), default="Conakry")
    commune = Column(String(100), nullable=True)  # Matoto, Kaloum, etc.
    neighborhood = Column(String(100), nullable=True)
    
    # Statut
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    is_featured = Column(Boolean, default=False)  # Annonce sponsorisée
    is_urgent = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    
    # Livraison
    delivery_available = Column(Boolean, default=False)
    delivery_fee = Column(Float, default=0.0)
    pickup_available = Column(Boolean, default=True)
    
    # Paiement
    accepts_mobilepay = Column(Boolean, default=True)
    accepts_cash = Column(Boolean, default=True)
    
    # Relations
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller = relationship("User", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="product")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Expiration annonce
    
    def __repr__(self):
        return f"<Product {self.title} - {self.price} GNF>"

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="images")