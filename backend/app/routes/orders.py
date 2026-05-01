"""
Routes de gestion des commandes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.middleware.auth_middleware import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.order_schema import (
    OrderCreate, OrderStatusUpdate, DeliveryConfirmation,
    OrderCancelRequest, OrderResponse, OrderDetailResponse,
    OrderTrackingResponse
)
from app.services.order_service import OrderService

router = APIRouter()
order_service = OrderService()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle commande"""
    order = await order_service.create_order(db, current_user.id, order_data)
    return order

@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Détails d'une commande"""
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    # Vérifier que l'utilisateur est impliqué dans la commande
    if current_user.id not in [order.customer_id, order.merchant_id] and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return order

@router.get("/", response_model=List[OrderResponse])
async def get_my_orders(
    role: str = Query("customer", enum=["customer", "merchant"]),
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste des commandes de l'utilisateur"""
    orders = await order_service.get_user_orders(
        db, current_user.id, role, status, page, limit
    )
    return orders

@router.put("/{order_id}/status", response_model=OrderResponse)
@require_role([UserRole.MERCHANT, UserRole.ADMIN])
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour le statut d'une commande (marchand)"""
    order = await order_service.update_order_status(
        db, order_id, status_update.status, status_update.note, current_user.id
    )
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order

@router.post("/{order_id}/confirm-delivery", response_model=OrderDetailResponse)
async def confirm_delivery(
    order_id: int,
    confirmation: DeliveryConfirmation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    CLIENT confirme la livraison → DÉCLENCHE LE PAIEMENT AU MARCHAND
    Point critique du workflow MobilePay
    """
    result = await order_service.confirm_delivery_and_release_payment(
        db, order_id, current_user.id, confirmation
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result["order"]

@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    cancel_request: OrderCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Annuler une commande (si éligible)"""
    order = await order_service.cancel_order(
        db, order_id, current_user.id, cancel_request.reason
    )
    if not order:
        raise HTTPException(status_code=400, detail="Commande non annulable")
    return order

@router.get("/{order_id}/tracking", response_model=OrderTrackingResponse)
async def track_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suivi de commande en temps réel"""
    tracking = await order_service.get_order_tracking(db, order_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return tracking

@router.get("/{order_id}/payment-status")
async def get_payment_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vérifier le statut du paiement d'une commande"""
    status = await order_service.get_payment_status(db, order_id)
    return status