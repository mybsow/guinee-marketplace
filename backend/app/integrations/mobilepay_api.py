"""
Client API MobilePay Guinée
Gère les appels à l'API MobilePay pour:
- Initier un paiement client
- Vérifier un paiement
- Effectuer un virement marchand
- Rembourser un paiement
"""
import httpx
import hashlib
import hmac
import json
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from app.config.mobilepay_config import mobilepay_settings

class MobilePayAPI:
    def __init__(self):
        self.api_key = mobilepay_settings.MOBILEPAY_API_KEY
        self.api_secret = mobilepay_settings.MOBILEPAY_API_SECRET
        self.base_url = mobilepay_settings.MOBILEPAY_BASE_URL
        self.merchant_id = mobilepay_settings.MOBILEPAY_MERCHANT_ID
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_signature(self, data: Dict) -> str:
        """Générer la signature HMAC pour les requêtes"""
        message = json.dumps(data, sort_keys=True)
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, data: Dict = None) -> Dict:
        """Headers HTTP pour les requêtes API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Merchant-ID": self.merchant_id,
        }
        
        if data:
            headers["X-Signature"] = self._generate_signature(data)
        
        return headers
    
    async def initiate_payment(
        self,
        amount: float,
        phone_number: str,
        reference: str,
        description: str = ""
    ) -> Dict:
        """
        Initier un paiement client MobilePay
        
        Args:
            amount: Montant en GNF
            phone_number: Numéro MobilePay du payeur
            reference: Référence unique de la transaction
            description: Description du paiement
        """
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "currency": "GNF",
            "phone_number": phone_number,
            "reference": reference,
            "description": description,
            "callback_url": f"https://api.guineemarket.gn/api/webhooks/mobilepay",
            "return_url": f"https://guineemarket.gn/payment/callback"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/payments/initiate",
                json=payload,
                headers=self._get_headers(payload)
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Paiement initié: {reference}")
                return {
                    "success": True,
                    "transaction_id": data.get("transaction_id"),
                    "status": data.get("status"),
                    "message": data.get("message")
                }
            else:
                logger.error(f"❌ Erreur API MobilePay: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Erreur {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"❌ Exception MobilePay: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def verify_payment(self, transaction_id: str) -> Dict:
        """Vérifier le statut d'un paiement"""
        try:
            response = await self.client.get(
                f"{self.base_url}/payments/{transaction_id}/status",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "ERROR", "message": response.text}
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification paiement: {str(e)}")
            return {"status": "ERROR", "message": str(e)}
    
    async def merchant_payout(
        self,
        amount: float,
        phone_number: str,
        reference: str,
        description: str = ""
    ) -> Dict:
        """
        Effectuer un virement au marchand
        
        Args:
            amount: Montant à virer (montant net après commission)
            phone_number: Numéro MobilePay du marchand
            reference: Référence unique du virement
            description: Description du virement
        """
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "currency": "GNF",
            "recipient_phone": phone_number,
            "reference": reference,
            "description": description,
            "type": "merchant_payout"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/payouts/merchant",
                json=payload,
                headers=self._get_headers(payload)
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Payout effectué: {reference} - {amount} GNF → {phone_number}")
                return {
                    "success": True,
                    "transaction_id": data.get("transaction_id"),
                    "status": data.get("status")
                }
            else:
                logger.error(f"❌ Erreur payout: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Erreur {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"❌ Exception payout: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def refund_payment(
        self,
        transaction_id: str,
        amount: float,
        reason: str = ""
    ) -> Dict:
        """Rembourser un paiement"""
        payload = {
            "transaction_id": transaction_id,
            "amount": amount,
            "reason": reason
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/payments/refund",
                json=payload,
                headers=self._get_headers(payload)
            )
            
            if response.status_code == 200:
                return {"success": True, **response.json()}
            else:
                return {"success": False, "message": response.text}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def check_transaction_status(self, transaction_id: str) -> Dict:
        """Vérifier le statut d'une transaction"""
        try:
            response = await self.client.get(
                f"{self.base_url}/transactions/{transaction_id}",
                headers=self._get_headers()
            )
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """Fermer le client HTTP"""
        await self.client.aclose()