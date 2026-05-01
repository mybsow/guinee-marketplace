"""
Routes de paiement MobilePay
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.payment_schema import (
    PaymentInitiate, PaymentVerify, PaymentResponse,
    PayoutResponse, TransactionHistory
)
from app.services.payment_service import PaymentService

router = APIRouter()
payment_service = PaymentService()

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(
    payment_data: PaymentInitiate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initier un paiement MobilePay
    Le fond sera SÉQUESTRÉ jusqu'à confirmation de livraison
    """
    payment = await payment_service.initiate_mobilepay_payment(
        db, current_user.id, payment_data
    )
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'initier le paiement"
        )
    
    return payment

@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    verification: PaymentVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vérifier et confirmer un paiement MobilePay"""
    payment = await payment_service.verify_mobilepay_payment(
        db, verification
    )
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vérification du paiement échouée"
        )
    
    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Détails d'un paiement"""
    payment = await payment_service.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    return payment

@router.post("/{order_id}/release", response_model=PayoutResponse)
async def release_payment_to_merchant(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Libérer le paiement au marchand (après confirmation livraison)
    Cette action est automatique lors de la confirmation client
    """
    # Vérifier que la commande est au statut DELIVERED et confirmée
    payout = await payment_service.release_funds_to_merchant(db, order_id)
    
    if not payout:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de libérer les fonds"
        )
    
    return payout

@router.get("/history", response_model=TransactionHistory)
async def get_payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Historique des transactions de l'utilisateur"""
    history = await payment_service.get_user_transaction_history(db, current_user.id)
    return history

@router.get("/status/{transaction_id}")
async def check_payment_status(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """Vérifier le statut d'une transaction MobilePay"""
    status = await payment_service.check_transaction_status(db, transaction_id)
    return status