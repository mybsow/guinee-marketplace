"""
Service de calcul des commissions
"""
from typing import Dict
from decimal import Decimal, ROUND_HALF_UP
from app.config.settings import settings

class CommissionService:
    def __init__(self):
        self.base_rate = settings.PLATFORM_COMMISSION_RATE
        self.min_commission = settings.MIN_COMMISSION_GNF
    
    def calculate_commission(
        self,
        amount: float,
        category: str = None
    ) -> float:
        """
        Calculer la commission de la plateforme
        
        Args:
            amount: Montant de la transaction en GNF
            category: Catégorie du produit (optionnel)
        
        Returns:
            Commission en GNF
        """
        # Taux de commission par catégorie
        category_rates = {
            "electronics": 0.08,
            "vehicles": 0.12,
            "real_estate": 0.15,
            "fashion": 0.10,
            "food": 0.07,
            "services": 0.10,
        }
        
        # Déterminer le taux applicable
        rate = category_rates.get(category, self.base_rate)
        
        # Calculer la commission
        commission = amount * rate
        
        # Appliquer le minimum
        if commission < self.min_commission:
            commission = self.min_commission
        
        # Arrondir à l'entier supérieur
        commission = int(Decimal(str(commission)).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        ))
        
        return commission
    
    def calculate_merchant_amount(
        self,
        total_amount: float,
        delivery_fee: float = 0,
        category: str = None
    ) -> Dict:
        """
        Calculer le montant net pour le marchand
        
        Returns:
            Dict avec le détail des montants
        """
        commission = self.calculate_commission(total_amount, category)
        merchant_amount = total_amount - commission
        
        return {
            "total_amount": total_amount,
            "delivery_fee": delivery_fee,
            "commission": commission,
            "commission_rate": self.base_rate,
            "merchant_amount": merchant_amount
        }
    
    def get_commission_breakdown(self, amount: float) -> Dict:
        """Obtenir le détail de la commission"""
        return {
            "amount": amount,
            "base_rate": f"{self.base_rate * 100}%",
            "commission": self.calculate_commission(amount),
            "net_amount": amount - self.calculate_commission(amount),
            "min_commission": self.min_commission,
            "currency": "GNF"
        }