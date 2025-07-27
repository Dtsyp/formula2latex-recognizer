import os
import sys
from decimal import Decimal

import pytest

# Добавляем src в Python path для тестов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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
        
        # Create user
        created_user = repo.create_user("test@example.com", "password123")
        
        # Get user by email
        found_user = repo.get_by_email("test@example.com")
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "test@example.com"

    def test_get_user_by_id(self, test_db):
        repo = UserRepository(test_db)
        
        # Create user
        created_user = repo.create_user("test@example.com", "password123")
        
        # Get user by ID
        found_user = repo.get_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.email == "test@example.com"

    def test_verify_password(self, test_db):
        repo = UserRepository(test_db)
        
        user = repo.create_user("test@example.com", "password123")
        
        # Get the actual hashed password from DB to test verification
        from infrastructure.models import User as UserModel
        user_model = test_db.query(UserModel).filter(UserModel.email == "test@example.com").first()
        
        assert repo.verify_password("password123", user_model.password) is True
        assert repo.verify_password("wrongpassword", user_model.password) is False


class TestWalletRepository:
    
    def test_get_wallet_by_owner_id(self, test_db):
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        # Create user (which creates wallet automatically)
        user = user_repo.create_user("test@example.com", "password123")
        
        # Get wallet by owner ID
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        assert wallet is not None
        assert wallet.owner_id == user.id
        assert wallet.balance == Decimal("0")

    def test_update_balance(self, test_db):
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        # Create user and get wallet
        user = user_repo.create_user("test@example.com", "password123")
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        # Update balance
        new_balance = Decimal("100.50")
        wallet_repo.update_balance(wallet.id, new_balance)
        
        # Verify balance updated
        updated_wallet = wallet_repo.get_by_id(wallet.id)
        assert updated_wallet.balance == new_balance

    def test_wallet_transactions(self, test_db):
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        # Create user and get wallet
        user = user_repo.create_user("test@example.com", "password123")
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        # Test top up
        top_up_amount = Decimal("50.00")
        txn = wallet.top_up(top_up_amount)
        wallet_repo.add_transaction(txn)
        wallet_repo.update_balance(wallet.id, wallet.balance)
        
        # Verify transaction was added
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
        
        # Create model
        created_model = repo.create_model("TestModel", Decimal("5.00"))
        
        # Get model by ID
        found_model = repo.get_by_id(created_model.id)
        
        assert found_model is not None
        assert found_model.name == "TestModel"
        assert found_model.credit_cost == Decimal("5.00")

    def test_get_active_models(self, test_db):
        repo = MLModelRepository(test_db)
        
        # Create multiple models
        model1 = repo.create_model("Model1", Decimal("5.00"))
        model2 = repo.create_model("Model2", Decimal("10.00"))
        
        # Get active models
        active_models = repo.get_active_models()
        
        assert len(active_models) == 2
        model_names = [model.name for model in active_models]
        assert "Model1" in model_names
        assert "Model2" in model_names


class TestIntegrationScenarios:
    
    def test_user_wallet_transaction_flow(self, test_db):
        """Test complete flow: create user, top up wallet, spend credits"""
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        # Create user
        user = user_repo.create_user("test@example.com", "password123")
        wallet = wallet_repo.get_by_owner_id(user.id)
        
        # Top up wallet
        top_up_amount = Decimal("100.00")
        top_up_txn = wallet.top_up(top_up_amount)
        wallet_repo.add_transaction(top_up_txn)
        wallet_repo.update_balance(wallet.id, wallet.balance)
        
        # Verify balance
        updated_wallet = wallet_repo.get_by_owner_id(user.id)
        assert updated_wallet.balance == Decimal("100.00")
        
        # Spend credits
        spend_amount = Decimal("25.00")
        spend_txn = updated_wallet.spend(spend_amount)
        wallet_repo.add_transaction(spend_txn)
        wallet_repo.update_balance(wallet.id, updated_wallet.balance)
        
        # Verify final balance and transactions
        final_wallet = wallet_repo.get_by_owner_id(user.id)
        assert final_wallet.balance == Decimal("75.00")
        assert len(final_wallet.transactions) == 2

    def test_admin_operations(self, test_db):
        """Test admin-specific operations"""
        user_repo = UserRepository(test_db)
        wallet_repo = WalletRepository(test_db)
        
        # Create admin and regular user
        admin = user_repo.create_user("admin@example.com", "password123", role="admin")
        user = user_repo.create_user("user@example.com", "password123")
        
        assert isinstance(admin, Admin)
        assert isinstance(user, User)
        
        # Admin tops up user's wallet
        user_wallet = wallet_repo.get_by_owner_id(user.id)
        top_up_txn = admin.top_up_user(user, Decimal("50.00"))
        wallet_repo.add_transaction(top_up_txn)
        wallet_repo.update_balance(user_wallet.id, user_wallet.balance)
        
        # Verify user's wallet was topped up
        updated_user_wallet = wallet_repo.get_by_owner_id(user.id)
        assert updated_user_wallet.balance == Decimal("50.00")
        
        # Admin can view user transactions
        transactions = admin.view_user_transactions(user)
        assert len(transactions) >= 1