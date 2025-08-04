from decimal import Decimal
from uuid import uuid4
import pytest
import datetime

from domain.user import User, Admin
from domain.wallet import Wallet, TopUpTransaction, SpendTransaction
from infrastructure.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyWalletRepository,
    SQLAlchemyMLModelRepository
)


class TestSQLAlchemyUserRepository:
    
    def test_create_user(self, test_db):
        repo = SQLAlchemyUserRepository(test_db)
        
        user = repo.create_user("test@example.com", "hashed_password", "user")
        
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.role == "user"
        assert user.is_active is True
        assert user.id is not None

    def test_create_admin(self, test_db):
        repo = SQLAlchemyUserRepository(test_db)
        
        admin = repo.create_user("admin@example.com", "hashed_password", "admin")
        
        assert admin.email == "admin@example.com"
        assert admin.role == "admin"
        assert isinstance(admin, Admin)

    def test_get_by_email(self, test_db):
        repo = SQLAlchemyUserRepository(test_db)
        
        created_user = repo.create_user("test@example.com", "hashed_password", "user")
        found_user = repo.get_by_email("test@example.com")
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "test@example.com"

    def test_get_by_email_not_found(self, test_db):
        repo = SQLAlchemyUserRepository(test_db)
        
        user = repo.get_by_email("nonexistent@example.com")
        
        assert user is None

    def test_get_by_id(self, test_db):
        repo = SQLAlchemyUserRepository(test_db)
        
        created_user = repo.create_user("test@example.com", "hashed_password", "user")
        found_user = repo.get_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "test@example.com"

    def test_update_user(self, test_db):
        repo = SQLAlchemyUserRepository(test_db)
        
        created_user = repo.create_user("test@example.com", "hashed_password", "user")
        
        updated_user = User(
            id=created_user.id,
            email="updated@example.com",
            password_hash="new_hashed_password",
            role="user",
            is_active=False
        )
        
        result = repo.update_user(updated_user)
        
        assert result.email == "updated@example.com"
        assert result.password_hash == "new_hashed_password"
        assert result.is_active is False

    def test_delete_user(self, test_db):
        repo = SQLAlchemyUserRepository(test_db)
        
        created_user = repo.create_user("test@example.com", "hashed_password", "user")
        success = repo.delete_user(created_user.id)
        
        assert success is True
        
        deleted_user = repo.get_by_id(created_user.id)
        assert deleted_user is None


class TestSQLAlchemyWalletRepository:
    
    def test_create_wallet(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "hashed_password", "user")
        wallet = wallet_repo.create_wallet(user.id, Decimal("0"))
        
        assert wallet.owner_id == user.id
        assert wallet.balance == Decimal("0")
        assert wallet.id is not None

    def test_get_by_owner_id(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "hashed_password", "user")
        created_wallet = wallet_repo.create_wallet(user.id, Decimal("100.00"))
        
        found_wallet = wallet_repo.get_by_owner_id(user.id)
        
        assert found_wallet is not None
        assert found_wallet.id == created_wallet.id
        assert found_wallet.balance == Decimal("100.00")

    def test_update_balance(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "hashed_password", "user")
        wallet = wallet_repo.create_wallet(user.id, Decimal("50.00"))
        
        updated_wallet = wallet_repo.update_balance(wallet.id, Decimal("100.00"))
        
        assert updated_wallet.balance == Decimal("100.00")

    def test_add_topup_transaction(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "hashed_password", "user")
        wallet = wallet_repo.create_wallet(user.id, Decimal("0"))
        
        transaction = TopUpTransaction(
            id=uuid4(),
            wallet_id=wallet.id,
            amount=Decimal("50.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("50.00")
        )
        
        added_transaction = wallet_repo.add_transaction(transaction)
        
        assert added_transaction.amount == Decimal("50.00")
        assert added_transaction.wallet_id == wallet.id

    def test_add_spend_transaction(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "hashed_password", "user")
        wallet = wallet_repo.create_wallet(user.id, Decimal("100.00"))
        
        transaction = SpendTransaction(
            id=uuid4(),
            wallet_id=wallet.id,
            amount=Decimal("25.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("75.00")
        )
        
        added_transaction = wallet_repo.add_transaction(transaction)
        
        assert added_transaction.amount == Decimal("25.00")
        assert added_transaction.wallet_id == wallet.id

    def test_get_transactions(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        
        user = user_repo.create_user("test@example.com", "hashed_password", "user")
        wallet = wallet_repo.create_wallet(user.id, Decimal("0"))
        
        topup_transaction = TopUpTransaction(
            id=uuid4(),
            wallet_id=wallet.id,
            amount=Decimal("100.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("100.00")
        )
        wallet_repo.add_transaction(topup_transaction)
        
        spend_transaction = SpendTransaction(
            id=uuid4(),
            wallet_id=wallet.id,
            amount=Decimal("25.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("75.00")
        )
        wallet_repo.add_transaction(spend_transaction)
        
        transactions = wallet_repo.get_transactions(wallet.id, limit=10)
        
        assert len(transactions) == 2
        assert transactions[0].amount == Decimal("25.00")
        assert transactions[1].amount == Decimal("100.00")


class TestSQLAlchemyMLModelRepository:
    
    def test_create_model(self, test_db):
        repo = SQLAlchemyMLModelRepository(test_db)
        
        model = repo.create_model("Test Model", Decimal("5.00"), True)
        
        assert model.name == "Test Model"
        assert model.credit_cost == Decimal("5.00")
        assert model.id is not None

    def test_get_by_id(self, test_db):
        repo = SQLAlchemyMLModelRepository(test_db)
        
        created_model = repo.create_model("Test Model", Decimal("5.00"), True)
        found_model = repo.get_by_id(created_model.id)
        
        assert found_model is not None
        assert found_model.id == created_model.id
        assert found_model.name == "Test Model"

    def test_get_all_active(self, test_db):
        repo = SQLAlchemyMLModelRepository(test_db)
        
        active_model = repo.create_model("Active Model", Decimal("5.00"), True)
        inactive_model = repo.create_model("Inactive Model", Decimal("3.00"), False)
        
        active_models = repo.get_all_active()
        
        assert len(active_models) == 1
        assert active_models[0].id == active_model.id
        assert active_models[0].name == "Active Model"

    def test_deactivate_model(self, test_db):
        repo = SQLAlchemyMLModelRepository(test_db)
        
        model = repo.create_model("Test Model", Decimal("5.00"), True)
        success = repo.deactivate_model(model.id)
        
        assert success is True
        
        active_models = repo.get_all_active()
        assert len(active_models) == 0