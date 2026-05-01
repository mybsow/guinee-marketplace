"""
Service de gestion des commandes
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, Dict
from datetime import datetime
from loguru import logger
import random
import string

from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.order_schema import OrderCreate, DeliveryConfirmation
from app.services.payment_service import PaymentService
from app.services.commission_service import CommissionService
from app.services.notification_service import NotificationService

class OrderService:
    def __init__(self):
        self.payment_service = PaymentService()
        self.commission_service = CommissionService()
        self.notification = NotificationService()
    
    def _generate_reference(self) -> str:
        """Générer une référence unique de commande"""
        prefix = "CMD"
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}-{random_part}"
    
    async def create_order(self, db: Session, customer_id: int, order_data: OrderCreate) -> Order:
        """Créer une nouvelle commande"""
        # Vérifier le produit
        product = db.query(Product).filter(
            Product.id == order_data.product_id,
            Product.status == ProductStatus.ACTIVE
        ).first()
        
        if not product:
            raise ValueError("Produit non disponible")
        
        if product.seller_id == customer_id:
            raise ValueError("Vous ne pouvez pas acheter votre propre produit")
        
        # Calculer les montants
        total_amount = product.price * order_data.quantity
        delivery_fee = product.delivery_fee if product.delivery_available else 0
        
        # Calculer la commission plateforme
        commission = self.commission_service.calculate_commission(total_amount)
        merchant_amount = total_amount - delivery_fee - commission
        
        # Créer la commande
        order = Order(
            reference=self._generate_reference(),
            customer_id=customer_id,
            merchant_id=product.seller_id,
            product_id=product.id,
            quantity=order_data.quantity,
            unit_price=product.price,
            total_amount=total_amount,
            delivery_fee=delivery_fee,
            platform_commission=commission,
            merchant_amount=merchant_amount,
            delivery_address=order_data.delivery_address,
            delivery_city=order_data.delivery_city,
            delivery_phone=order_data.delivery_phone,
            delivery_notes=order_data.delivery_notes,
            status=OrderStatus.PENDING_PAYMENT
        )
        
        db.add(order)
        
        # Réserver le produit (optionnel)
        # product.status = ProductStatus.RESERVED
        
        db.commit()
        db.refresh(order)
        
        logger.info(f"✅ Commande créée: {order.reference}")
        
        # Notifier le marchand
        await self.notification.notify_new_order(db, order)
        
        return order
    
    async def confirm_delivery_and_release_payment(
        self,
        db: Session,
        order_id: int,
        customer_id: int,
        confirmation: DeliveryConfirmation
    ) -> Dict:
        """
        CRITIQUE: Confirmation livraison → Libération paiement au marchand
        """
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.customer_id == customer_id
        ).first()
        
        if not order:
            return {"success": False, "message": "Commande non trouvée"}
        
        if order.status != OrderStatus.DELIVERED:
            return {
                "success": False,
                "message": f"La commande doit être livrée avant confirmation. Statut actuel: {order.status}"
            }
        
        if order.customer_confirmed:
            return {"success": False, "message": "Livraison déjà confirmée"}
        
        # Vérifier le code de confirmation
        if confirmation.confirmation_code != order.reference[-6:]:
            return {"success": False, "message": "Code de confirmation invalide"}
        
        try:
            # Marquer comme confirmé
            order.customer_confirmed = True
            order.customer_confirmed_at = datetime.utcnow()
            order.status = OrderStatus.COMPLETED
            order.completed_at = datetime.utcnow()
            
            # Ajouter note/évaluation si fournie
            if confirmation.rating:
                # Mettre à jour la réputation du marchand
                merchant = db.query(User).filter(User.id == order.merchant_id).first()
                if merchant:
                    merchant.total_reviews += 1
                    merchant.rating = (
                        (merchant.rating * (merchant.total_reviews - 1) + confirmation.rating)
                        / merchant.total_reviews
                    )
            
            db.commit()
            
            logger.info(f"🎉 Livraison confirmée pour commande {order.reference}")
            
            # 🚨 DÉCLENCHEMENT DU PAIEMENT AU MARCHAND
            payout_result = await self.payment_service.release_funds_to_merchant(
                db, order.id
            )
            
            if payout_result:
                logger.info(f"💰 Paiement libéré au marchand: {order.merchant_amount} GNF")
                # Notifier le marchand
                await self.notification.notify_payment_released(db, order)
                # Notifier le client
                await self.notification.notify_order_completed(db, order)
            
            return {
                "success": True,
                "message": "Livraison confirmée et paiement libéré au marchand",
                "order": order
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erreur confirmation livraison: {str(e)}")
            return {"success": False, "message": f"Erreur: {str(e)}"}
    
    async def update_order_status(
        self,
        db: Session,
        order_id: int,
        new_status: OrderStatus,
        note: Optional[str],
        merchant_id: int
    ) -> Optional[Order]:
        """Mettre à jour le statut (par le marchand)"""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.merchant_id == merchant_id
        ).first()
        
        if not order:
            return None
        
        # Vérifier la transition de statut valide
        valid_transitions = {
            OrderStatus.PAYMENT_RECEIVED: [OrderStatus.PROCESSING],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            raise ValueError(f"Transition de statut invalide: {order.status} → {new_status}")
        
        order.status = new_status
        
        # Mettre à jour les timestamps
        if new_status == OrderStatus.PROCESSING:
            pass  # Déjà en préparation
        elif new_status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.utcnow()
            order.merchant_confirmed = True
        elif new_status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()
            # 🚨 Notifier le client de confirmer la réception
            await self.notification.notify_delivery_confirmation_required(db, order)
        
        db.commit()
        db.refresh(order)
        
        logger.info(f"📦 Statut commande {order.reference}: {new_status}")
        
        return order
    
    async def cancel_order(
        self,
        db: Session,
        order_id: int,
        user_id: int,
        reason: str
    ) -> Optional[Order]:
        """Annuler une commande"""
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            return None
        
        # Vérifier les droits d'annulation
        if user_id not in [order.customer_id, order.merchant_id]:
            raise ValueError("Non autorisé à annuler cette commande")
        
        if not order.can_be_cancelled:
            raise ValueError("Cette commande ne peut plus être annulée")
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        order.cancellation_reason = reason
        
        # Si le paiement a été reçu, déclencher le remboursement
        if order.status == OrderStatus.PAYMENT_RECEIVED:
            await self.payment_service.refund_payment(db, order.id)
        
        # Remettre le produit en vente
        product = db.query(Product).filter(Product.id == order.product_id).first()
        if product:
            product.status = ProductStatus.ACTIVE
        
        db.commit()
        db.refresh(order)
        
        logger.info(f"❌ Commande annulée: {order.reference}")
        
        return order
    
    async def get_order_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        """Récupérer une commande par ID"""
        return db.query(Order).filter(Order.id == order_id).first()
    
    async def get_user_orders(
        self,
        db: Session,
        user_id: int,
        role: str,
        status: Optional[str],
        page: int,
        limit: int
    ):
        """Récupérer les commandes d'un utilisateur"""
        query = db.query(Order)
        
        if role == "customer":
            query = query.filter(Order.customer_id == user_id)
        else:
            query = query.filter(Order.merchant_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        query = query.order_by(Order.created_at.desc())
        
        return query.offset((page - 1) * limit).limit(limit).all()
    
    async def get_order_tracking(self, db: Session, order_id: int) -> Optional[Dict]:
        """Obtenir le suivi détaillé d'une commande"""
        order = await self.get_order_by_id(db, order_id)
        if not order:
            return None
        
        # Construire la timeline
        timeline = [
            {"date": order.created_at, "event": "Commande créée", "status": "info"},
        ]
        
        if order.paid_at:
            timeline.append({"date": order.paid_at, "event": "Paiement reçu", "status": "success"})
        
        if order.shipped_at:
            timeline.append({"date": order.shipped_at, "event": "Commande expédiée", "status": "info"})
        
        if order.delivered_at:
            timeline.append({"date": order.delivered_at, "event": "Commande livrée", "status": "warning"})
        
        if order.completed_at:
            timeline.append({"date": order.completed_at, "event": "Commande terminée", "status": "success"})
        
        # Déterminer les prochaines actions possibles
        next_actions = []
        if order.status == OrderStatus.DELIVERED and not order.customer_confirmed:
            next_actions.append({
                "action": "confirm_delivery",
                "label": "Confirmer la réception",
                "code_hint": f"Code: XXXXXX (6 derniers caractères de la référence)"
            })
        
        return {
            "order": order,
            "timeline": timeline,
            "current_status": order.status,
            "next_possible_actions": next_actions
        }
    
    async def get_payment_status(self, db: Session, order_id: int) -> Dict:
        """Vérifier le statut du paiement"""
        order = await self.get_order_by_id(db, order_id)
        if not order:
            raise ValueError("Commande non trouvée")
        
        payments = order.payments
        
        return {
            "order_id": order.id,
            "order_reference": order.reference,
            "order_status": order.status,
            "payments": [
                {
                    "id": p.id,
                    "reference": p.reference,
                    "amount": p.amount,
                    "status": p.status,
                    "method": p.payment_method,
                    "created_at": p.created_at
                }
                for p in payments
            ],
            "customer_confirmed": order.customer_confirmed,
            "funds_released": order.status == OrderStatus.COMPLETED
        }