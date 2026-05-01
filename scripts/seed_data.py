"""
Script de seeding de la base de données
"""
import sys
sys.path.insert(0, 'backend')

from app.config.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.product import Product, ProductCategory, ProductStatus
from app.utils.security import hash_password

def seed_database():
    db = SessionLocal()
    
    try:
        # Créer les tables
        Base.metadata.create_all(bind=engine)
        
        # Admin
        admin = User(
            phone_number="+224620000001",
            email="admin@guineemarket.gn",
            full_name="Admin GuinéeMarket",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_phone_verified=True,
            is_active=True
        )
        db.add(admin)
        
        # Marchand test
        merchant = User(
            phone_number="+224620000002",
            email="marchand@test.gn",
            full_name="Marchand Test",
            password_hash=hash_password("test123"),
            role=UserRole.MERCHANT,
            is_phone_verified=True,
            business_name="Boutique Test",
            is_active=True
        )
        db.add(merchant)
        
        # Client test
        customer = User(
            phone_number="+224620000003",
            email="client@test.gn",
            full_name="Client Test",
            password_hash=hash_password("test123"),
            role=UserRole.CUSTOMER,
            is_phone_verified=True,
            is_active=True
        )
        db.add(customer)
        
        db.commit()
        
        # Produits test
        products = [
            Product(
                title="iPhone 13 Pro Max",
                description="iPhone 13 Pro Max 256Go, excellent état, avec chargeur et coque",
                price=8000000,
                category=ProductCategory.ELECTRONICS,
                condition="used",
                city="Conakry",
                seller_id=merchant.id,
                status=ProductStatus.ACTIVE,
                delivery_available=True,
                delivery_fee=50000
            ),
            Product(
                title="Toyota Corolla 2019",
                description="Toyota Corolla 2019, boîte automatique, climatisation, très bon état",
                price=85000000,
                category=ProductCategory.VEHICLES,
                condition="used",
                city="Conakry",
                seller_id=merchant.id,
                status=ProductStatus.ACTIVE
            ),
            Product(
                title="Robe traditionnelle guinéenne",
                description="Magnifique robe en wax, fait main, toutes tailles disponibles",
                price=150000,
                category=ProductCategory.FASHION,
                condition="new",
                city="Conakry",
                seller_id=merchant.id,
                status=ProductStatus.ACTIVE,
                delivery_available=True,
                delivery_fee=20000
            ),
            Product(
                title="Sac de riz local 50kg",
                description="Riz guinéen de qualité supérieure, récolte 2024",
                price=350000,
                category=ProductCategory.FOOD,
                condition="new",
                city="Kankan",
                seller_id=merchant.id,
                status=ProductStatus.ACTIVE,
                delivery_available=True,
                delivery_fee=30000
            ),
        ]
        
        for product in products:
            db.add(product)
        
        db.commit()
        
        print("✅ Base de données seedée avec succès!")
        print(f"   Admin: +224620000001 / admin123")
        print(f"   Marchand: +224620000002 / test123")
        print(f"   Client: +224620000003 / test123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()