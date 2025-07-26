from decimal import Decimal
from sqlalchemy.orm import Session
from infrastructure.database import SessionLocal, engine, Base
from infrastructure.models import *
from infrastructure.repositories import UserRepository, MLModelRepository, WalletRepository
import os

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

def init_demo_data():
    """Initialize database with demo data"""
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        model_repo = MLModelRepository(db)
        wallet_repo = WalletRepository(db)
        
        # Check if demo data already exists
        existing_admin = user_repo.get_by_email("admin@formula2latex.com")
        if existing_admin:
            print("❌ Demo data already exists, skipping initialization")
            return
        
        # Create demo admin
        print("👤 Creating demo admin...")
        admin = user_repo.create_user(
            email="admin@formula2latex.com",
            password="admin123",
            role="admin"
        )
        print(f"✅ Admin created: {admin.email}")
        
        # Create demo user
        print("👤 Creating demo user...")
        user = user_repo.create_user(
            email="user@formula2latex.com",
            password="user123"
        )
        print(f"✅ User created: {user.email}")
        
        # Top up demo user's wallet
        print("💰 Adding credits to demo user...")
        user_wallet = wallet_repo.get_by_owner_id(user.id)
        top_up_txn = user_wallet.top_up(Decimal("100.00"))
        wallet_repo.add_transaction(top_up_txn)
        wallet_repo.update_balance(user_wallet.id, user_wallet.balance)
        print(f"✅ Added 100.00 credits to user wallet")
        
        # Create demo ML models
        print("🤖 Creating demo ML models...")
        
        models_data = [
            ("Basic OCR Model", Decimal("2.50"), "Простая модель для распознавания печатного текста"),
            ("Advanced LaTeX Model", Decimal("5.00"), "Продвинутая модель для распознавания формул"),
            ("Premium Deep Learning Model", Decimal("10.00"), "Премиум модель с высокой точностью"),
        ]
        
        for name, cost, description in models_data:
            model = model_repo.create_model(name, cost)
            print(f"✅ Created model: {name} (cost: {cost} credits)")
        
        print("\n🎉 Demo data initialization completed successfully!")
        print("\n📊 Summary:")
        print(f"👨‍💼 Admin: admin@formula2latex.com / admin123")
        print(f"👤 User: user@formula2latex.com / user123 (100.00 credits)")
        print(f"🤖 ML Models: {len(models_data)} models created")
        
    except Exception as e:
        print(f"❌ Error during demo data initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def reset_database():
    """Drop all tables and recreate them"""
    print("🔄 Resetting database...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")
    create_tables()

def main():
    """Main initialization function"""
    print("🚀 Starting database initialization...")
    
    # Create tables if they don't exist
    create_tables()
    
    # Initialize with demo data
    init_demo_data()
    
    print("\n✨ Database initialization complete!")

if __name__ == "__main__":
    main()