"""
Passerelle SMS pour la Guinée
Supporte Orange Guinée et autres opérateurs locaux
"""
from typing import Dict, Optional
from abc import ABC, abstractmethod
import httpx
from loguru import logger
from app.config.settings import settings

class SMSProvider(ABC):
    @abstractmethod
    def send_sms(self, phone_number: str, message: str) -> Dict:
        pass

class OrangeGuineeSMS(SMSProvider):
    """Orange Guinée SMS API"""
    
    def __init__(self):
        self.api_key = settings.SMS_API_KEY
        self.sender_id = settings.SMS_SENDER_ID
        self.base_url = "https://api.orange.com/sms/v2"
    
    def send_sms(self, phone_number: str, message: str) -> Dict:
        """Envoyer un SMS via Orange Guinée"""
        try:
            # Simulation de l'API Orange Guinée
            logger.info(f"📱 [Orange SMS] Envoi à {phone_number}: {message[:50]}...")
            
            # En environnement de développement, simuler le succès
            if settings.DEBUG:
                return {
                    "success": True,
                    "message_id": f"ORANGE-{datetime.utcnow().timestamp()}",
                    "status": "sent"
                }
            
            # Version production avec vrai appel API
            import requests
            response = requests.post(
                f"{self.base_url}/messages",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "outboundSMSMessageRequest": {
                        "address": f"tel:+224{phone_number}",
                        "senderAddress": f"tel:{self.sender_id}",
                        "outboundSMSTextMessage": {
                            "message": message
                        }
                    }
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("resourceReference", {}).get("resourceURL"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur Orange SMS: {str(e)}")
            return {"success": False, "error": str(e)}

class GenericSMSProvider(SMSProvider):
    """Fournisseur SMS générique pour autres opérateurs"""
    
    def send_sms(self, phone_number: str, message: str) -> Dict:
        """Envoyer SMS via un fournisseur générique"""
        # Pour le développement, utilisation d'un service HTTP générique
        logger.info(f"📱 [Generic SMS] Envoi à {phone_number}: {message[:50]}...")
        
        return {
            "success": True,
            "message_id": f"GEN-{datetime.utcnow().timestamp()}",
            "status": "sent"
        }

class SMSGateway:
    """Passerelle SMS principale - Route selon l'opérateur"""
    
    def __init__(self):
        self.providers = {
            "orange": OrangeGuineeSMS(),
            "generic": GenericSMSProvider()
        }
    
    def detect_operator(self, phone_number: str) -> str:
        """Détecter l'opérateur à partir du numéro"""
        # Préfixes Guinée:
        # Orange: 77, 78
        # MTN: 66, 67
        # Cellcom: 62, 63
        clean_number = phone_number.replace("+224", "").replace(" ", "")
        
        if clean_number.startswith(("77", "78")):
            return "orange"
        elif clean_number.startswith(("66", "67")):
            return "mtn"
        elif clean_number.startswith(("62", "63")):
            return "cellcom"
        else:
            return "generic"
    
    def send_sms(self, phone_number: str, message: str) -> Dict:
        """Envoyer un SMS via le bon opérateur"""
        operator = self.detect_operator(phone_number)
        
        # Pour l'instant, utiliser le provider générique
        # Plus tard, router selon l'opérateur
        provider = "generic"
        
        return self.providers[provider].send_sms(phone_number, message)

def get_sms_gateway() -> SMSGateway:
    """Factory pour la passerelle SMS"""
    return SMSGateway()

# Pour les imports circulaires
from datetime import datetime