"""
Validateurs de données
"""
import re
from typing import Optional
from datetime import datetime

def validate_email(email: str) -> bool:
    """Valider une adresse email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_price(price: float) -> bool:
    """Valider un prix en GNF"""
    return 1000 <= price <= 1000000000  # 1,000 à 1,000,000,000 GNF

def validate_title(title: str) -> bool:
    """Valider un titre d'annonce"""
    return 5 <= len(title.strip()) <= 200

def validate_description(desc: str) -> bool:
    """Valider une description"""
    return 20 <= len(desc.strip()) <= 5000

def validate_product_category(category: str) -> bool:
    """Valider une catégorie de produit"""
    valid_categories = [
        "electronics", "vehicles", "real_estate", "fashion",
        "home_garden", "sports", "food", "services", "jobs",
        "animals", "other"
    ]
    return category in valid_categories

def validate_guinea_city(city: str) -> bool:
    """Valider une ville guinéenne"""
    major_cities = [
        "conakry", "kankan", "labé", "nzérékoré", "kindia",
        "boké", "mamou", "faranah", "dabola", "guéckédou"
    ]
    return city.lower() in major_cities