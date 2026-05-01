"""
Service de paiement MobilePay Guinée
Gère le workflow: Client paie → Séquestre → Livraison → Paiement marchand
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict
from datetime import datetime, timedelta
from loguru import logger
import uuid

from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus, Payout, PayoutStatus
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.schemas.payment_schema import PaymentInitiate, PaymentVerify, MobilePayWebhook
from app.integrations.mobilepay_api import MobilePayAPI
from app.services.commission_service import CommissionService
from app.services.notification_service import NotificationService
from app.config.settings import settings

class PaymentService:
    def __init__(self):
        self.mobilepay = MobilePayAPI()
        self.commission = CommissionService()
        self.notification = NotificationService()
    
    def _generate_reference(self, prefix: str = "PAY") -> str:
        """Générer une référence unique"""
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
    
    async def initiate_mobilepay_payment(
        self,
        db: Session,
        user_id: int,
        payment_data: PaymentInitiate
    ) -> Optional[Payment]:
        """
        ÉTAPE 1: Initier un paiement MobilePay
        Le montant est DÉBITÉ du client mais SÉQUESTRÉ par la plateforme
        """
        # Vérifier la commande
        order = db.query(Order).filter(
            Order.id == payment_data.order_id,
            Order.customer_id == user_id,
            Order.status == OrderStatus.PENDING_PAYMENT
        ).first()
        
        if not order:
            logger.error(f"❌ Commande {payment_data.order_id} non trouvée ou non payable")
            return None
        
        # Vérifier qu'aucun paiement n'est déjà en cours
        existing_payment = db.query(Payment).filter(
            Payment.order_id == order.id,
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING])
        ).first()
        
        if existing_payment:
            logger.warning(f"⚠️ Paiement déjà en cours: {existing_payment.reference}")
            return existing_payment
        
        # Créer l'enregistrement de paiement
        payment = Payment(
            reference=self._generate_reference("PAY"),
            order_id=order.id,
            user_id=user_id,
            amount=order.total_amount + order.delivery_fee,
            currency="GNF",
            status=PaymentStatus.PENDING,
            payment_method="mobilepay",
            payer_phone=payment_data.phone_number
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # Appeler l'API MobilePay pour initier le paiement
        try:
            mobilepay_response = await self.mobilepay.initiate_payment(
                amount=payment.amount,
                phone_number=payment_data.phone_number,
                reference=payment.reference,
                description=f"Commande {order.reference}"
            )
            
            if mobilepay_response.get("success"):
                payment.mobilepay_transaction_id = mobilepay_response.get("transaction_id")
                payment.status = PaymentStatus.PROCESSING
                payment.metadata_json = str(mobilepay_response)
                
                # Mettre à jour la commande
                order.status = OrderStatus.PENDING_PAYMENT
                
                db.commit()
                db.refresh(payment)
                
                logger.info(f"💳 Paiement initié: {payment.reference} - {payment.amount} GNF")
                
                # Envoyer notification de paiement en attente
                await self.notification.notify_payment_initiated(db, payment, order)
                
                return payment
            else:
                payment.status = PaymentStatus.FAILED
                payment.error_message = mobilepay_response.get("message", "Erreur inconnue")
                db.commit()
                logger.error(f"❌ Échec initiation paiement: {payment.error_message}")
                return None
                
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.error_message = str(e)
            db.commit()
            logger.error(f"❌ Exception paiement: {str(e)}")
            return None
    
    async def verify_mobilepay_payment(
        self,
        db: Session,
        verification: PaymentVerify
    ) -> Optional[Payment]:
        """
        ÉTAPE 2: Vérifier et confirmer un paiement MobilePay
        Une fois confirmé, le fond est SÉQUESTRÉ
        """
        payment = db.query(Payment).filter(
            Payment.reference == verification.payment_reference
        ).first()
        
        if not payment:
            logger.error(f"❌ Paiement non trouvé: {verification.payment_reference}")
            return None
        
        # Vérifier avec MobilePay
        try:
            verification_response = await self.mobilepay.verify_payment(
                transaction_id=verification.transaction_id
            )
            
            if verification_response.get("status") == "SUCCESS":
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = datetime.utcnow()
                payment.mobilepay_transaction_id = verification.transaction_id
                
                # Mettre à jour la commande
                order = db.query(Order).filter(Order.id == payment.order_id).first()
                if order:
                    order.status = OrderStatus.PAYMENT_RECEIVED
                    order.paid_at = datetime.utcnow()
                    
                    # Créer la transaction de commission
                    self._create_commission_transaction(db, order)
                
                db.commit()
                db.refresh(payment)
                
                logger.info(f"✅ Paiement confirmé: {payment.reference} - FONDS SÉQUESTRÉS")
                
                # Notifications
                await self.notification.notify_payment_received(db, payment, order)
                
                # Notifier le marchand de préparer la commande
                if order:
                    await self.notification.notify_merchant_to_prepare(db, order)
                
                return payment
            else:
                payment.status = PaymentStatus.FAILED
                payment.error_message = "Vérification échouée"
                db.commit()
                logger.error(f"❌ Vérification paiement échouée: {verification_response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception vérification paiement: {str(e)}")
            return None
    
    async def release_funds_to_merchant(
        self,
        db: Session,
        order_id: int
    ) -> Optional[Payout]:
        """
        ÉTAPE 3: Libérer les fonds au marchand APRÈS confirmation de livraison
        Point CRITIQUE du workflow - Le paiement n'est libéré QUE si la commande est livrée
        """
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.status == OrderStatus.COMPLETED,
            Order.customer_confirmed == True  # DOUBLE VÉRIFICATION
        ).first()
        
        if not order:
            logger.error(f"❌ Commande {order_id} non éligible pour libération des fonds")
            return None
        
        # Vérifier qu'aucun payout n'a déjà été fait
        existing_payout = db.query(Payout).filter(
            Payout.order_id == order.id,
            Payout.status.in_([PayoutStatus.COMPLETED, PayoutStatus.PROCESSING])
        ).first()
        
        if existing_payout:
            logger.warning(f"⚠️ Payout déjà effectué: {existing_payout.reference}")
            return existing_payout
        
        # Vérifier le délai de sécurité
        if settings.MERCHANT_PAYOUT_DELAY_HOURS > 0:
            if order.completed_at:
                earliest_payout = order.completed_at + timedelta(
                    hours=settings.MERCHANT_PAYOUT_DELAY_HOURS
                )
                if datetime.utcnow() < earliest_payout:
                    logger.info(f"⏰ Payout en attente du délai de sécurité: {earliest_payout}")
                    # Programmer le payout pour plus tard
                    return None
        
        # Récupérer le marchand
        merchant = db.query(User).filter(User.id == order.merchant_id).first()
        if not merchant:
            logger.error(f"❌ Marchand non trouvé: {order.merchant_id}")
            return None
        
        # Créer le payout
        payout = Payout(
            reference=self._generate_reference("PYT"),
            order_id=order.id,
            merchant_id=merchant.id,
            amount=order.merchant_amount,
            commission_amount=order.platform_commission,
            status=PayoutStatus.PENDING,
            merchant_phone=merchant.phone_number
        )
        
        db.add(payout)
        db.commit()
        db.refresh(payout)
        
        # Appeler l'API MobilePay pour le virement marchand
        try:
            payout_response = await self.mobilepay.merchant_payout(
                amount=payout.amount,
                phone_number=merchant.phone_number,
                reference=payout.reference,
                description=f"Paiement commande {order.reference}"
            )
            
            if payout_response.get("success"):
                payout.status = PayoutStatus.COMPLETED
                payout.completed_at = datetime.utcnow()
                payout.mobilepay_reference = payout_response.get("transaction_id")
                
                # Mettre à jour le solde du marchand
                merchant.balance_gnf += payout.amount
                merchant.total_sales += 1
                
                # Créer la transaction comptable
                self._create_payout_transaction(db, payout, merchant)
                
                db.commit()
                db.refresh(payout)
                
                logger.info(f"💰 PAIEMENT LIBÉRÉ AU MARCHAND: {payout.amount} GNF → {merchant.phone_number}")
                
                # Notifier le marchand du paiement reçu
                await self.notification.notify_merchant_paid(db, payout, merchant)
                
                return payout
            else:
                payout.status = PayoutStatus.FAILED
                payout.error_message = payout_response.get("message", "Échec virement")
                db.commit()
                logger.error(f"❌ Échec payout: {payout.error_message}")
                
                # ALERTE: Paiement échoué, intervention manuelle nécessaire
                await self.notification.notify_admin_payout_failed(db, payout)
                
                return None
                
        except Exception as e:
            payout.status = PayoutStatus.FAILED
            payout.error_message = str(e)
            db.commit()
            logger.error(f"❌ Exception payout: {str(e)}")
            return None
    
    async def refund_payment(
        self,
        db: Session,
        order_id: int,
        reason: str = "Commande annulée"
    ) -> Optional[Payment]:
        """Rembourser un paiement (si commande annulée avant livraison)"""
        payment = db.query(Payment).filter(
            Payment.order_id == order_id,
            Payment.status == PaymentStatus.COMPLETED
        ).first()
        
        if not payment:
            return None
        
        try:
            refund_response = await self.mobilepay.refund_payment(
                transaction_id=payment.mobilepay_transaction_id,
                amount=payment.amount,
                reason=reason
            )
            
            if refund_response.get("success"):
                payment.status = PaymentStatus.REFUNDED
                
                # Mettre à jour la commande
                order = db.query(Order).filter(Order.id == order_id).first()
                if order:
                    order.status = OrderStatus.REFUNDED
                
                db.commit()
                logger.info(f"↩️ Remboursement effectué: {payment.reference}")
                return payment
                
        except Exception as e:
            logger.error(f"❌ Erreur remboursement: {str(e)}")
            return None
    
    def _create_commission_transaction(self, db: Session, order: Order):
        """Enregistrer la commission de la plateforme"""
        transaction = Transaction(
            reference=self._generate_reference("COM"),
            type=TransactionType.COMMISSION,
            amount=order.platform_commission,
            user_id=order.merchant_id,
            order_id=order.id,
            description=f"Commission sur commande {order.reference}"
        )
        db.add(transaction)
    
    def _create_payout_transaction(self, db: Session, payout: Payout, merchant: User):
        """Enregistrer la transaction de paiement marchand"""
        transaction = Transaction(
            reference=self._generate_reference("TXN"),
            type=TransactionType.PAYOUT,
            amount=payout.amount,
            balance_before=merchant.balance_gnf - payout.amount,
            balance_after=merchant.balance_gnf,
            user_id=merchant.id,
            order_id=payout.order_id,
            description=f"Paiement marchand - Commande {payout.reference}"
        )
        db.add(transaction)
    
    async def get_payment_by_id(self, db: Session, payment_id: int) -> Optional[Payment]:
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    async def get_user_transaction_history(self, db: Session, user_id: int) -> Dict:
        """Historique complet des transactions"""
        payments = db.query(Payment).filter(Payment.user_id == user_id).all()
        payouts = db.query(Payout).filter(Payout.merchant_id == user_id).all()
        
        total_spent = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED)
        total_earned = sum(p.amount for p in payouts if p.status == PayoutStatus.COMPLETED)
        total_commission = sum(p.commission_amount for p in payouts if p.status == PayoutStatus.COMPLETED)
        
        return {
            "payments": payments,
            "payouts": payouts,
            "total_spent": total_spent,
            "total_earned": total_earned,
            "total_commission": total_commission
        }
    
    async def check_transaction_status(self, db: Session, transaction_id: str) -> Dict:
        """Vérifier le statut d'une transaction MobilePay"""
        return await self.mobilepay.check_transaction_status(transaction_id)
    
    # Handlers Webhook
    async def handle_payment_success_webhook(self, db: Session, webhook: MobilePayWebhook):
        """Webhook: Paiement réussi"""
        payment = db.query(Payment).filter(
            Payment.reference == webhook.reference
        ).first()
        
        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            payment.mobilepay_transaction_id = webhook.transaction_id
            
            order = db.query(Order).filter(Order.id == payment.order_id).first()
            if order:
                order.status = OrderStatus.PAYMENT_RECEIVED
                order.paid_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"📩 Webhook: Paiement confirmé {webhook.reference}")
    
    async def handle_payment_failed_webhook(self, db: Session, webhook: MobilePayWebhook):
        """Webhook: Paiement échoué"""
        payment = db.query(Payment).filter(
            Payment.reference == webhook.reference
        ).first()
        
        if payment:
            payment.status = PaymentStatus.FAILED
            db.commit()
            logger.warning(f"📩 Webhook: Paiement échoué {webhook.reference}")
    
    async def handle_payout_completed_webhook(self, db: Session, webhook: MobilePayWebhook):
        """Webhook: Payout complété"""
        payout = db.query(Payout).filter(
            Payout.reference == webhook.reference
        ).first()
        
        if payout:
            payout.status = PayoutStatus.COMPLETED
            payout.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"📩 Webhook: Payout complété {webhook.reference}")
    
    async def handle_payout_failed_webhook(self, db: Session, webhook: MobilePayWebhook):
        """Webhook: Payout échoué - ALERTE CRITIQUE"""
        payout = db.query(Payout).filter(
            Payout.reference == webhook.reference
        ).first()
        
        if payout:
            payout.status = PayoutStatus.FAILED
            db.commit()
            logger.error(f"🚨 Webhook: Payout ÉCHOUÉ {webhook.reference} - Intervention requise!")
            await self.notification.notify_admin_payout_failed(db, payout)