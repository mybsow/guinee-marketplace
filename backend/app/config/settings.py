"""
Configuration générale de l'application
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "GuinéeMarket"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    SECRET_KEY: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Database
    DATABASE_URL: str
    DATABASE_TEST_URL: str = "sqlite:///./test.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # MobilePay Guinea
    MOBILEPAY_API_KEY: str
    MOBILEPAY_API_SECRET: str
    MOBILEPAY_BASE_URL: str = "https://api.mobilepayguinee.com/v1"
    MOBILEPAY_MERCHANT_ID: str
    MOBILEPAY_WEBHOOK_SECRET: str
    
    # Platform
    PLATFORM_COMMISSION_RATE: float = 0.10
    MIN_COMMISSION_GNF: int = 5000
    MERCHANT_PAYOUT_DELAY_HOURS: int = 24
    
    # SMS Gateway
    SMS_API_KEY: Optional[str] = None
    SMS_SENDER_ID: str = "GuineeMarket"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    
    # Currency
    DEFAULT_CURRENCY: str = "GNF"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()