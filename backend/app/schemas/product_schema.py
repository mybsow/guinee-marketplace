"""
Schémas Produit/Annonce
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.product import ProductCategory, ProductStatus

class ProductImageCreate(BaseModel):
    url: str
    is_primary: bool = False

class ProductCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    price: float = Field(..., gt=0)
    category: ProductCategory
    condition: str = "used"
    city: str = "Conakry"
    commune: Optional[str] = None
    neighborhood: Optional[str] = None
    is_negotiable: bool = True
    delivery_available: bool = False
    delivery_fee: float = 0.0
    images: List[ProductImageCreate] = []
    
    @validator('price')
    def validate_price(cls, v):
        if v < 1000:  # Minimum 1000 GNF
            raise ValueError('Prix minimum: 1000 GNF')
        if v > 1000000000:  # Maximum 1 milliard GNF
            raise ValueError('Prix maximum: 1,000,000,000 GNF')
        return v

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    is_negotiable: Optional[bool] = None
    status: Optional[ProductStatus] = None

class ProductSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[ProductCategory] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    city: Optional[str] = None
    condition: Optional[str] = None
    sort_by: str = "newest"  # newest, price_asc, price_desc, popular
    page: int = 1
    limit: int = 20

class ProductResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    currency: str
    category: ProductCategory
    condition: str
    city: str
    commune: Optional[str] = None
    status: ProductStatus
    views_count: int
    is_featured: bool
    delivery_available: bool
    delivery_fee: float
    seller: 'UserResponse'
    images: List[ProductImageCreate]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    total: int
    page: int
    limit: int
    products: List[ProductResponse]