"""
Service de notifications (SMS, Email, Push)
"""
from sqlalchemy.orm import Session
from typing import Optional
from loguru import logger
import random

from app.models.notification import Notification, NotificationType
from app.models.order import Order
from app.models.payment import Payment, Payout
from app.models.user import User
from app.integrations.sms_gateway import SMSGateway, get_sms_gateway

class NotificationService:
    def __init__(self):
        self.sms_gateway = get_sms_gateway()
    
    async def send_sms(
        self,
        db: Session,
        user_id: int,
        phone_number: str,
        message: str,
        order_id: Optional[int] = None
    ) -> bool:
        """Envoyer un SMS via la passerelle locale"""
        try:
            # Créer la notification en base
            notification = Notification(
                user_id=user_id,
                type=NotificationType.SMS,
                message=message,
                recipient=phone_number,
                order_id=order_id,
                is_sent=False
            )
            db.add(notification)
            db.commit()
            
            # Envoyer le SMS
            result = self.sms_gateway.send_sms(phone_number, message)
            
            if result["success"]:
                notification.is_sent = True
                notification.sent_at = datetime.utcnow()
                notification.provider_message_id = result.get("message_id")
                db.commit()
                logger.info(f"📱 SMS envoyé à {phone_number}")
                return True
            else:
                notification.error_message = result.get("error")
                db.commit()
                logger.error(f"❌ Échec SMS: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception SMS: {str(e)}")
            return False
    
    async def send_verification_code(
        self,
        db: Session,
        user: User,
        code: str
    ):
        """Envoyer le code de vérification téléphone"""
        message = f"GuineeMarket: Votre code de verification est {code}. Ne partagez ce code avec personne."
        await self.send_sms(db, user.id, user.phone_number, message)
    
    async def notify_new_order(self, db: Session, order: Order):
        """Notifier le marchand d'une nouvelle commande"""
        message = (
            f"GuineeMarket: Nouvelle commande #{order.reference}!\n"
            f"Montant: {order.total_amount} GNF\n"
            f"Produit: {order.product_id}\n"
            f"Connectez-vous pour confirmer."
        )
        await self.send_sms(db, order.merchant_id, order.merchant.phone_number, message, order.id)
    
    async def notify_payment_initiated(self, db: Session, payment: Payment, order: Order):
        """Notifier le client que le paiement est en cours"""
        message = (
            f"GuineeMarket: Paiement de {payment.amount} GNF en cours.\n"
            f"Reference: {payment.reference}\n"
            f"Vous recevrez une confirmation sous peu."
        )
        await self.send_sms(db, payment.user_id, payment.payer_phone, message, order.id)
    
    async def notify_payment_received(self, db: Session, payment: Payment, order: Order):
        """Notifier que le paiement est reçu (fonds séquestrés)"""
        # Notifier le client
        message_client = (
            f"GuineeMarket: Paiement confirme! {payment.amount} GNF.\n"
            f"Commande #{order.reference}\n"
            f"Le vendeur prepare votre commande."
        )
        await self.send_sms(db, order.customer_id, order.customer.phone_number, message_client, order.id)
        
        # Notifier le marchand
        message_merchant = (
            f"GuineeMarket: Paiement recu pour commande #{order.reference}!\n"
            f"Montant: {order.total_amount} GNF\n"
            f"Veuillez preparer la commande pour expedition."
        )
        await self.send_sms(db, order.merchant_id, order.merchant.phone_number, message_merchant, order.id)
    
    async def notify_merchant_to_prepare(self, db: Session, order: Order):
        """Rappel au marchand de préparer la commande"""
        message = (
            f"GuineeMarket: RAPPEL - Commande #{order.reference} en attente.\n"
            f"Veuillez mettre a jour le statut de la commande."
        )
        await self.send_sms(db, order.merchant_id, order.merchant.phone_number, message, order.id)
    
    async def notify_delivery_confirmation_required(self, db: Session, order: Order):
        """
        CRITIQUE: Notifier le client de confirmer la livraison
        Cette confirmation déclenche le paiement au marchand
        """
        confirmation_code = order.reference[-6:]
        message = (
            f"GuineeMarket: Votre commande #{order.reference} est livree!\n"
            f"Code de confirmation: {confirmation_code}\n"
            f"Confirmez la reception pour liberer le paiement au vendeur.\n"
            f"Connectez-vous: guineemarket.gn/orders/{order.id}"
        )
        await self.send_sms(db, order.customer_id, order.customer.phone_number, message, order.id)
    
    async def notify_payment_released(self, db: Session, order: Order):
        """Notifier le marchand que le paiement est libéré"""
        message = (
            f"GuineeMarket: PAIEMENT LIBERE! {order.merchant_amount} GNF\n"
            f"Commande #{order.reference}\n"
            f"Le montant sera credite sur votre compte MobilePay."
        )
        await self.send_sms(db, order.merchant_id, order.merchant.phone_number, message, order.id)
    
    async def notify_order_completed(self, db: Session, order: Order):
        """Notifier le client que la commande est terminée"""
        message = (
            f"GuineeMarket: Commande #{order.reference} terminee!\n"
            f"Merci pour votre achat.\n"
            f"Notez votre experience pour aider les autres acheteurs."
        )
        await self.send_sms(db, order.customer_id, order.customer.phone_number, message, order.id)
    
    async def notify_merchant_paid(self, db: Session, payout: Payout, merchant: User):
        """Notifier le marchand du virement reçu"""
        message = (
            f"GuineeMarket: VIREMENT RECU! {payout.amount} GNF\n"
            f"Reference: {payout.reference}\n"
            f"Nouveau solde: {merchant.balance_gnf} GNF\n"
            f"Merci pour votre confiance!"
        )
        await self.send_sms(db, merchant.id, merchant.phone_number, message)
    
    async def notify_admin_payout_failed(self, db: Session, payout: Payout):
        """ALERTE ADMIN: Échec de paiement marchand"""
        message = (
            f"🚨 ALERTE: Paiement marchand ECHOUE!\n"
            f"Payout: {payout.reference}\n"
            f"Montant: {payout.amount} GNF\n"
            f"Marchand: {payout.merchant_phone}\n"
            f"Action immediate requise!"
        )
        # Envoyer aux administrateurs
        admins = db.query(User).filter(User.role == "admin").all()
        for admin in admins:
            await self.send_sms(db, admin.id, admin.phone_number, message)