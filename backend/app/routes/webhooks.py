"""
Webhooks MobilePay pour callbacks automatiques
"""
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.payment_schema import MobilePayWebhook
from app.services.payment_service import PaymentService
from app.services.order_service import OrderService
from app.config.mobilepay_config import mobilepay_settings
import hashlib
import hmac
from loguru import logger

router = APIRouter()
payment_service = PaymentService()
order_service = OrderService()

@router.post("/mobilepay")
async def mobilepay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook MobilePay pour recevoir les notifications de paiement
    Endpoint critique : DOIT être sécurisé
    """
    # Vérifier la signature MobilePay
    signature = request.headers.get("X-MobilePay-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Signature manquante")
    
    body = await request.body()
    
    # Vérifier le secret
    expected_signature = hmac.new(
        mobilepay_settings.MOBILEPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        logger.error("❌ Signature webhook invalide")
        raise HTTPException(status_code=401, detail="Signature invalide")
    
    # Traiter l'événement
    try:
        event_data = await request.json()
        webhook = MobilePayWebhook(**event_data)
        
        logger.info(f"📩 Webhook reçu: {webhook.event} - {webhook.reference}")
        
        # Router selon le type d'événement
        if webhook.event == "payment.success":
            await payment_service.handle_payment_success_webhook(db, webhook)
            
        elif webhook.event == "payment.failed":
            await payment_service.handle_payment_failed_webhook(db, webhook)
            
        elif webhook.event == "payout.completed":
            await payment_service.handle_payout_completed_webhook(db, webhook)
            
        elif webhook.event == "payout.failed":
            await payment_service.handle_payout_failed_webhook(db, webhook)
        
        return {"status": "success", "message": "Webhook traité"}
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mobilepay/test")
async def test_webhook(
    webhook: MobilePayWebhook,
    db: Session = Depends(get_db)
):
    """Endpoint de test pour les webhooks (désactiver en production)"""
    logger.info(f"🧪 Test webhook: {webhook.event}")
    return {"status": "test", "data": webhook.dict()}