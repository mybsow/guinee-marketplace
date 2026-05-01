"""
Fonctions utilitaires
"""
import re
import unicodedata
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

def format_gnf(amount: float) -> str:
    """Formater un montant en GNF avec séparateurs"""
    return f"{int(amount):,} GNF".replace(",", " ")

def round_gnf(amount: float) -> int:
    """Arrondir au GNF supérieur"""
    return int(Decimal(str(amount)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def validate_guinea_phone(phone: str) -> bool:
    """Valider un numéro de téléphone guinéen"""
    pattern = r'^(\+224)?[67]\d{7}$'
    clean = re.sub(r'[\s-]', '', phone)
    return bool(re.match(pattern, clean))

def normalize_phone(phone: str) -> str:
    """Normaliser un numéro au format +224XXXXXXXXX"""
    clean = re.sub(r'[\s-]', '', phone)
    if not clean.startswith('+224'):
        clean = '+224' + clean
    return clean

def slugify(text: str) -> str:
    """Créer un slug à partir d'un texte"""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def generate_reference(prefix: str = "REF") -> str:
    """Générer une référence unique"""
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def get_time_ago(dt: datetime) -> str:
    """Retourne le temps écoulé en français"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "À l'instant"
    elif diff < timedelta(hours=1):
        minutes = int(diff.seconds / 60)
        return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
    elif diff < timedelta(days=1):
        hours = int(diff.seconds / 3600)
        return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"Il y a {days} jour{'s' if days > 1 else ''}"
    else:
        return dt.strftime("%d/%m/%Y")

def paginate(page: int, limit: int, total: int) -> dict:
    """Calculer les métadonnées de pagination"""
    total_pages = max(1, (total + limit - 1) // limit)
    
    return {
        "current_page": page,
        "limit": limit,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None
    }