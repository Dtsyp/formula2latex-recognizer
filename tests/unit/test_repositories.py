from decimal import Decimal
import pytest

from domain import User, Admin
from infrastructure import UserRepository, WalletRepository, MLModelRepository


class TestUserRepository:
    
    def test_create_user(self, test_db):
        repo = UserRepository(test_db)
        
        user = repo.create_user("test@example.com", "password123")
        
        assert user is not None
        assert user.email == "test@example.com"
        assert user.wallet is not None
        assert user.wallet.balance == Decimal("0")

    def test_create_admin_user(self, test_db):
        repo = UserRepository(test_db)
        
        admin = repo.create_user("admin@example.com", "password123", role="admin")
        
        assert isinstance(admin, Admin)
        assert admin.email == "admin@example.com"
        assert admin.role == "admin"

    def test_get_user_by_email(self, test_db):
        repo = UserRepository(test_db)
        
        created_user = repo.create_user("test@example.com", "password123")
        found_user = repo.get_by_email("test@example.com")
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "test@example.com"

    def test_get_user_by_id(self, test_db):
        repo = UserRepository(test_db)
        
        created_user = repo.create_user("test@example.com", "password123")
        found_user = repo.get_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.email == "test@example.com"

    def test_verify_password(self, test_db):
        repo = UserRepository(test_db)
        
        user = repo.create_user("test@example.com", "password123")
        
        from infrastructure.models import User as UserModel
        user_model = test_db.query(UserModel).filter(UserModel.email == "test@example.com").first()
        
        assert repo.verify_password("password123", user_model.password) is True
        assert repo.verify_password("wrongpassword", user_model.password) is False


class TestWalletRepository:
    
    def test_get_wallet_by_owner_id(self, test_db):
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "password123")
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        assert wallet is not None
        assert wallet.owner_id == user.id
        assert wallet.balance == Decimal("0")

    def test_update_balance(self, test_db):
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "password123")
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        new_balance = Decimal("100.50")
        wallet_repo.update_balance(wallet.id, new_balance)
        
        updated_wallet = wallet_repo.get_by_id(wallet.id)
        assert updated_wallet.balance == new_balance

    def test_wallet_transactions(self, test_db):
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "password123")
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        top_up_amount = Decimal("50.00")
        txn = wallet.top_up(top_up_amount)
        wallet_repo.add_transaction(txn)
        wallet_repo.update_balance(wallet.id, wallet.balance)
        
        updated_wallet = wallet_repo.get_by_owner_id(user.id)
        assert len(updated_wallet.transactions) == 1
        assert updated_wallet.transactions[0].amount == top_up_amount


class TestMLModelRepository:
    
    def test_create_model(self, test_db):
        repo = MLModelRepository(test_db)
        
        model = repo.create_model("TestModel", Decimal("5.00"))
        
        assert model is not None
        assert model.name == "TestModel"
        assert model.credit_cost == Decimal("5.00")

    def test_get_model_by_id(self, test_db):
        repo = MLModelRepository(test_db)
        
        created_model = repo.create_model("TestModel", Decimal("5.00"))
        found_model = repo.get_by_id(created_model.id)
        
        assert found_model is not None
        assert found_model.name == "TestModel"
        assert found_model.credit_cost == Decimal("5.00")

    def test_get_active_models(self, test_db):
        repo = MLModelRepository(test_db)
        
        model1 = repo.create_model("Model1", Decimal("5.00"))
        model2 = repo.create_model("Model2", Decimal("10.00"))
        
        active_models = repo.get_active_models()
        
        assert len(active_models) == 2
        model_names = [model.name for model in active_models]
        assert "Model1" in model_names
        assert "Model2" in model_names