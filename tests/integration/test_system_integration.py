import pytest
from decimal import Decimal
from uuid import uuid4

from domain.user import User
from domain.services.user_service import UserAuthService
from domain.services.wallet_service import WalletManagementService
from infrastructure.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyWalletRepository,
    SQLAlchemyMLModelRepository
)
from infrastructure.services.password_service import BCryptPasswordService


class TestSystemIntegration:
    
    def test_user_registration_and_wallet_creation_flow(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        
        user = user_service.register_user("test@example.com", "StrongPassword123!")
        
        assert user.email == "test@example.com"
        assert user.is_active is True
        
        wallet = wallet_repo.get_by_owner_id(user.id)
        assert wallet is not None
        assert wallet.owner_id == user.id
        assert wallet.balance == Decimal("0")

    def test_user_authentication_flow(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        
        created_user = user_service.register_user("test@example.com", "StrongPassword123!")
        
        authenticated_user = user_service.authenticate_user("test@example.com", "StrongPassword123!")
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        
        failed_auth = user_service.authenticate_user("test@example.com", "WrongPassword")
        assert failed_auth is None

    def test_wallet_operations_flow(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        wallet_service = WalletManagementService(wallet_repo)
        
        user = user_service.register_user("test@example.com", "StrongPassword123!")
        
        initial_wallet = wallet_service.get_user_wallet(user)
        assert initial_wallet.balance == Decimal("0")
        
        topup_transaction = wallet_service.top_up_wallet(user, Decimal("100.00"), "Initial deposit")
        assert topup_transaction.amount == Decimal("100.00")
        assert topup_transaction.post_balance == Decimal("100.00")
        
        updated_wallet = wallet_service.get_user_wallet(user)
        assert updated_wallet.balance == Decimal("100.00")
        
        charge_transaction = wallet_service.charge_for_task(user, Decimal("25.00"), uuid4())
        assert charge_transaction.amount == Decimal("25.00")
        assert charge_transaction.post_balance == Decimal("75.00")
        
        final_wallet = wallet_service.get_user_wallet(user)
        assert final_wallet.balance == Decimal("75.00")
        
        transactions = wallet_service.get_transaction_history(user, 10)
        assert len(transactions) == 2
        assert transactions[0].amount == Decimal("25.00")  # Most recent first
        assert transactions[1].amount == Decimal("100.00")

    def test_insufficient_funds_flow(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        wallet_service = WalletManagementService(wallet_repo)
        
        user = user_service.register_user("test@example.com", "StrongPassword123!")
        
        wallet_service.top_up_wallet(user, Decimal("10.00"), "Small deposit")
        
        with pytest.raises(ValueError, match="Недостаточно средств"):
            wallet_service.charge_for_task(user, Decimal("50.00"), uuid4())
        
        wallet = wallet_service.get_user_wallet(user)
        assert wallet.balance == Decimal("10.00")  # Balance unchanged

    def test_password_change_flow(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        
        user = user_service.register_user("test@example.com", "OldPassword123!")
        
        auth_with_old = user_service.authenticate_user("test@example.com", "OldPassword123!")
        assert auth_with_old is not None
        
        success = user_service.change_password(user, "OldPassword123!", "NewPassword123!")
        assert success is True
        
        auth_with_old_after_change = user_service.authenticate_user("test@example.com", "OldPassword123!")
        assert auth_with_old_after_change is None
        
        auth_with_new = user_service.authenticate_user("test@example.com", "NewPassword123!")
        assert auth_with_new is not None

    def test_ml_model_repository_operations(self, test_db):
        model_repo = SQLAlchemyMLModelRepository(test_db)
        
        model1 = model_repo.create_model("TrOCR v1", Decimal("5.00"), True)
        model2 = model_repo.create_model("TrOCR v2", Decimal("7.50"), True)
        inactive_model = model_repo.create_model("Old Model", Decimal("3.00"), False)
        
        found_model = model_repo.get_by_id(model1.id)
        assert found_model.name == "TrOCR v1"
        assert found_model.credit_cost == Decimal("5.00")
        
        active_models = model_repo.get_all_active()
        assert len(active_models) == 2
        active_names = [model.name for model in active_models]
        assert "TrOCR v1" in active_names
        assert "TrOCR v2" in active_names
        assert "Old Model" not in active_names
        
        success = model_repo.deactivate_model(model1.id)
        assert success is True
        
        active_models_after = model_repo.get_all_active()
        assert len(active_models_after) == 1
        assert active_models_after[0].name == "TrOCR v2"

    def test_user_deactivation_flow(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        
        user = user_service.register_user("test@example.com", "StrongPassword123!")
        assert user.is_active is True
        
        auth_before = user_service.authenticate_user("test@example.com", "StrongPassword123!")
        assert auth_before is not None
        
        deactivated_user = user_service.deactivate_user(user)
        assert deactivated_user.is_active is False
        
        auth_after = user_service.authenticate_user("test@example.com", "StrongPassword123!")
        assert auth_after is None

    def test_email_change_flow(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        
        user = user_service.register_user("old@example.com", "StrongPassword123!")
        
        updated_user = user_service.change_email(user, "new@example.com")
        assert updated_user.email == "new@example.com"
        
        auth_with_new_email = user_service.authenticate_user("new@example.com", "StrongPassword123!")
        assert auth_with_new_email is not None
        
        auth_with_old_email = user_service.authenticate_user("old@example.com", "StrongPassword123!")
        assert auth_with_old_email is None

    def test_duplicate_email_registration_prevention(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        
        user_service.register_user("test@example.com", "FirstPassword123!")
        
        with pytest.raises(ValueError, match="уже существует"):
            user_service.register_user("test@example.com", "SecondPassword123!")

    def test_transaction_ordering(self, test_db):
        user_repo = SQLAlchemyUserRepository(test_db)
        wallet_repo = SQLAlchemyWalletRepository(test_db)
        password_service = BCryptPasswordService()
        
        user_service = UserAuthService(user_repo, wallet_repo, password_service)
        wallet_service = WalletManagementService(wallet_repo)
        
        user = user_service.register_user("test@example.com", "StrongPassword123!")
        
        wallet_service.top_up_wallet(user, Decimal("100.00"), "First topup")
        wallet_service.charge_for_task(user, Decimal("25.00"), uuid4())
        wallet_service.top_up_wallet(user, Decimal("50.00"), "Second topup")
        wallet_service.charge_for_task(user, Decimal("10.00"), uuid4())
        
        transactions = wallet_service.get_transaction_history(user, 10)
        assert len(transactions) == 4
        
        amounts = [t.amount for t in transactions]
        assert amounts == [Decimal("10.00"), Decimal("50.00"), Decimal("25.00"), Decimal("100.00")]