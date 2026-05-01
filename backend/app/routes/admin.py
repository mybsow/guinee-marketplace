"""
Routes d'administration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.config.database import get_db
from app.middleware.auth_middleware import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductStatus
from app.models.payment import Payment, PaymentStatus, Payout, PayoutStatus
from app.models.transaction import Transaction, TransactionType

router = APIRouter()

# Middleware admin obligatoire pour toutes les routes
@router.get("/dashboard")
@require_role([UserRole.ADMIN])
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Statistiques du tableau de bord admin"""
    
    # Période (30 derniers jours par défaut)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Utilisateurs
    total_users = db.query(func.count(User.id)).scalar()
    new_users = db.query(func.count(User.id)).filter(
        User.created_at >= thirty_days_ago
    ).scalar()
    active_merchants = db.query(func.count(User.id)).filter(
        User.role == UserRole.MERCHANT,
        User.is_active == True
    ).scalar()
    
    # Produits
    total_products = db.query(func.count(Product.id)).scalar()
    active_products = db.query(func.count(Product.id)).filter(
        Product.status == ProductStatus.ACTIVE
    ).scalar()
    new_products = db.query(func.count(Product.id)).filter(
        Product.created_at >= thirty_days_ago
    ).scalar()
    
    # Commandes
    total_orders = db.query(func.count(Order.id)).scalar()
    completed_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.COMPLETED
    ).scalar()
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status.in_([OrderStatus.PENDING_PAYMENT, OrderStatus.PAYMENT_RECEIVED])
    ).scalar()
    
    # Paiements
    total_payments = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.COMPLETED
    ).scalar() or 0
    
    recent_payments = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.COMPLETED,
        Payment.completed_at >= thirty_days_ago
    ).scalar() or 0
    
    # Commissions
    total_commissions = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.COMMISSION
    ).scalar() or 0
    
    recent_commissions = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.COMMISSION,
        Transaction.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Payouts en attente
    pending_payouts = db.query(func.sum(Payout.amount)).filter(
        Payout.status == PayoutStatus.PENDING
    ).scalar() or 0
    
    # Taux de conversion
    conversion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    
    # Commandes par jour (30 jours)
    orders_per_day = db.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('count')
    ).filter(
        Order.created_at >= thirty_days_ago
    ).group_by(
        func.date(Order.created_at)
    ).all()
    
    return {
        "users": {
            "total": total_users,
            "new_this_month": new_users,
            "active_merchants": active_merchants
        },
        "products": {
            "total": total_products,
            "active": active_products,
            "new_this_month": new_products
        },
        "orders": {
            "total": total_orders,
            "completed": completed_orders,
            "pending": pending_orders,
            "conversion_rate": round(conversion_rate, 2)
        },
        "finance": {
            "total_payments": total_payments,
            "recent_payments": recent_payments,
            "total_commissions": total_commissions,
            "recent_commissions": recent_commissions,
            "pending_payouts": pending_payouts,
            "platform_revenue": total_commissions,
            "revenue_this_month": recent_commissions
        },
        "charts": {
            "orders_per_day": [
                {"date": str(row.date), "count": row.count}
                for row in orders_per_day
            ]
        }
    }

@router.get("/users")
@require_role([UserRole.ADMIN])
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste de tous les utilisateurs"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%") |
            User.phone_number.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%")
        )
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "users": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "phone_number": u.phone_number,
                "email": u.email,
                "role": u.role,
                "is_verified": u.is_phone_verified,
                "is_active": u.is_active,
                "rating": u.rating,
                "total_sales": u.total_sales,
                "created_at": u.created_at
            }
            for u in users
        ]
    }

@router.put("/users/{user_id}/toggle-status")
@require_role([UserRole.ADMIN])
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activer/Désactiver un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {
        "message": f"Utilisateur {'activé' if user.is_active else 'désactivé'}",
        "is_active": user.is_active
    }

@router.put("/users/{user_id}/ban")
@require_role([UserRole.ADMIN])
async def ban_user(
    user_id: int,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bannir un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user.is_banned = True
    user.ban_reason = reason
    user.is_active = False
    db.commit()
    
    return {"message": "Utilisateur banni", "reason": reason}

@router.get("/products/moderation")
@require_role([UserRole.ADMIN])
async def get_products_for_moderation(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Produits en attente de modération"""
    query = db.query(Product)
    
    if status:
        query = query.filter(Product.status == status)
    
    total = query.count()
    products = query.order_by(Product.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "price": p.price,
                "category": p.category,
                "status": p.status,
                "seller_name": p.seller.full_name if p.seller else "N/A",
                "views": p.views_count,
                "created_at": p.created_at
            }
            for p in products
        ]
    }

@router.put("/products/{product_id}/moderate")
@require_role([UserRole.ADMIN])
async def moderate_product(
    product_id: int,
    action: str = Query(..., regex="^(approve|reject)$"),
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approuver ou rejeter un produit"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    if action == "approve":
        product.status = ProductStatus.ACTIVE
    else:
        product.status = ProductStatus.REJECTED
    
    db.commit()
    
    return {
        "message": f"Produit {'approuvé' if action == 'approve' else 'rejeté'}",
        "status": product.status
    }

@router.get("/transactions")
@require_role([UserRole.ADMIN])
async def get_all_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toutes les transactions de la plateforme"""
    query = db.query(Transaction)
    
    if type:
        query = query.filter(Transaction.type == type)
    
    if start_date:
        query = query.filter(Transaction.created_at >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(end_date))
    
    total = query.count()
    transactions = query.order_by(Transaction.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    
    # Résumé financier
    total_volume = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type.in_([TransactionType.COMMISSION, TransactionType.PAYOUT])
    ).scalar() or 0
    
    return {
        "total": total,
        "page": page,
        "total_volume": total_volume,
        "transactions": [
            {
                "id": t.id,
                "reference": t.reference,
                "type": t.type,
                "amount": t.amount,
                "user_id": t.user_id,
                "order_id": t.order_id,
                "description": t.description,
                "created_at": t.created_at
            }
            for t in transactions
        ]
    }

@router.get("/commissions")
@require_role([UserRole.ADMIN])
async def get_commissions_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rapport des commissions"""
    query = db.query(
        func.date(Transaction.created_at).label('date'),
        func.sum(Transaction.amount).label('total_commission'),
        func.count(Transaction.id).label('transaction_count')
    ).filter(
        Transaction.type == TransactionType.COMMISSION
    )
    
    if start_date:
        query = query.filter(Transaction.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(end_date))
    
    results = query.group_by(func.date(Transaction.created_at)).all()
    
    total_commission = sum(r.total_commission for r in results)
    
    return {
        "total_commission": total_commission,
        "daily_breakdown": [
            {
                "date": str(r.date),
                "commission": r.total_commission,
                "transactions": r.transaction_count
            }
            for r in results
        ]
    }

@router.get("/payouts/pending")
@require_role([UserRole.ADMIN])
async def get_pending_payouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Payouts en attente (nécessitent attention)"""
    payouts = db.query(Payout).filter(
        Payout.status == PayoutStatus.PENDING
    ).all()
    
    failed_payouts = db.query(Payout).filter(
        Payout.status == PayoutStatus.FAILED
    ).order_by(Payout.created_at.desc()).limit(20).all()
    
    return {
        "pending": [
            {
                "id": p.id,
                "reference": p.reference,
                "amount": p.amount,
                "merchant_phone": p.merchant_phone,
                "order_id": p.order_id,
                "created_at": p.created_at
            }
            for p in payouts
        ],
        "failed": [
            {
                "id": p.id,
                "reference": p.reference,
                "amount": p.amount,
                "error": p.error_message,
                "created_at": p.created_at
            }
            for p in failed_payouts
        ],
        "total_pending_amount": sum(p.amount for p in payouts)
    }