"""
Schémas Utilisateur
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
import re

class PhoneNumberMixin:
    @validator('phone_number')
    def validate_guinea_phone(cls, v):
        # Numéros Guinée: +224 XX XXX XX XX
        pattern = r'^(\+224)?[67]\d{7}$'
        clean_number = re.sub(r'[\s-]', '', v)
        if not re.match(pattern, clean_number):
            raise ValueError('Numéro de téléphone guinéen invalide')
        return clean_number

class UserCreate(BaseModel, PhoneNumberMixin):
    phone_number: str
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.CUSTOMER
    city: str = "Conakry"
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Mot de passe trop court')
        return v

class UserLogin(BaseModel):
    phone_number: str
    password: str

class PhoneVerification(BaseModel):
    phone_number: str
    verification_code: str = Field(..., min_length=6, max_length=6)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    
class UserKYCUpdate(BaseModel):
    national_id: str
    date_of_birth: str  # Format: YYYY-MM-DD
    address: str
    city: str

class UserResponse(BaseModel):
    id: int
    phone_number: str
    email: Optional[str] = None
    full_name: str
    role: UserRole
    is_phone_verified: bool
    is_kyc_verified: bool
    rating: float
    total_sales: int
    balance_gnf: float
    city: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"