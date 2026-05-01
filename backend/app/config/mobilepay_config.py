"""
Configuration spécifique MobilePay Guinée
"""
from pydantic_settings import BaseSettings
from typing import Dict, Optional
from decimal import Decimal

class MobilePaySettings(BaseSettings):
    """Paramètres de connexion à l'API MobilePay Guinée"""
    
    # API Credentials
    MOBILEPAY_API_KEY: str
    MOBILEPAY_API_SECRET: str
    MOBILEPAY_BASE_URL: str = "https://api.mobilepayguinee.com/v1"
    MOBILEPAY_MERCHANT_ID: str
    MOBILEPAY_WEBHOOK_SECRET: str
    
    # Endpoints API
    @property
    def initiate_payment_url(self) -> str:
        return f"{self.MOBILEPAY_BASE_URL}/payments/initiate"
    
    @property
    def check_payment_status_url(self) -> str:
        return f"{self.MOBILEPAY_BASE_URL}/payments/status"
    
    @property
    def merchant_payout_url(self) -> str:
        return f"{self.MOBILEPAY_BASE_URL}/payouts/merchant"
    
    @property
    def refund_url(self) -> str:
        return f"{self.MOBILEPAY_BASE_URL}/payments/refund"
    
    # Commission
    PLATFORM_COMMISSION_RATE: float = 0.10
    MIN_COMMISSION_GNF: int = 5000
    
    # Timeouts (secondes)
    PAYMENT_TIMEOUT: int = 300  # 5 minutes
    PAYOUT_TIMEOUT: int = 60
    
    # Taux de commission par catégorie
    CATEGORY_COMMISSION_RATES: Dict[str, float] = {
        "electronics": 0.08,
        "vehicles": 0.12,
        "real_estate": 0.15,
        "fashion": 0.10,
        "services": 0.10,
        "food": 0.07,
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

mobilepay_settings = MobilePaySettings()