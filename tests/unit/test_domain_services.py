from decimal import Decimal
from uuid import uuid4
import pytest
import datetime
from unittest.mock import Mock

from domain.user import User
from domain.wallet import Wallet, TopUpTransaction, SpendTransaction
from domain.services.user_service import UserAuthService
from domain.services.wallet_service import WalletManagementService


class TestUserAuthService:
    
    def test_register_user_success(self):
        mock_user_repo = Mock()
        mock_wallet_repo = Mock()
        mock_password_service = Mock()
        
        mock_user_repo.get_by_email.return_value = None
        mock_password_service.validate_password_strength.return_value = {'is_strong': True}
        mock_password_service.hash_password.return_value = "hashed_password"
        
        created_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password"
        )
        mock_user_repo.create_user.return_value = created_user
        
        service = UserAuthService(mock_user_repo, mock_wallet_repo, mock_password_service)
        result = service.register_user("test@example.com", "strongpassword123")
        
        assert result.email == "test@example.com"
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_password_service.validate_password_strength.assert_called_once_with("strongpassword123")
        mock_password_service.hash_password.assert_called_once_with("strongpassword123")
        mock_user_repo.create_user.assert_called_once_with("test@example.com", "hashed_password", "user")
        mock_wallet_repo.create_wallet.assert_called_once_with(created_user.id)

    def test_register_user_email_exists(self):
        mock_user_repo = Mock()
        mock_wallet_repo = Mock()
        mock_password_service = Mock()
        
        existing_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="existing_hash"
        )
        mock_user_repo.get_by_email.return_value = existing_user
        
        service = UserAuthService(mock_user_repo, mock_wallet_repo, mock_password_service)
        
        with pytest.raises(ValueError, match="Пользователь с email test@example.com уже существует"):
            service.register_user("test@example.com", "password123")

    def test_register_user_weak_password(self):
        mock_user_repo = Mock()
        mock_wallet_repo = Mock()
        mock_password_service = Mock()
        
        mock_user_repo.get_by_email.return_value = None
        mock_password_service.validate_password_strength.return_value = {
            'is_strong': False,
            'issues': ['Пароль слишком короткий', 'Нет заглавных букв']
        }
        
        service = UserAuthService(mock_user_repo, mock_wallet_repo, mock_password_service)
        
        with pytest.raises(ValueError, match="Пароль не соответствует требованиям"):
            service.register_user("test@example.com", "weak")

    def test_authenticate_user_success(self):
        mock_user_repo = Mock()
        mock_wallet_repo = Mock()
        mock_password_service = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            is_active=True
        )
        mock_user_repo.get_by_email.return_value = user
        mock_password_service.verify_password.return_value = True
        
        service = UserAuthService(mock_user_repo, mock_wallet_repo, mock_password_service)
        result = service.authenticate_user("test@example.com", "correct_password")
        
        assert result == user
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_password_service.verify_password.assert_called_once_with("correct_password", "hashed_password")

    def test_authenticate_user_wrong_password(self):
        mock_user_repo = Mock()
        mock_wallet_repo = Mock()
        mock_password_service = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            is_active=True
        )
        mock_user_repo.get_by_email.return_value = user
        mock_password_service.verify_password.return_value = False
        
        service = UserAuthService(mock_user_repo, mock_wallet_repo, mock_password_service)
        result = service.authenticate_user("test@example.com", "wrong_password")
        
        assert result is None

    def test_authenticate_user_inactive(self):
        mock_user_repo = Mock()
        mock_wallet_repo = Mock()
        mock_password_service = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com", 
            password_hash="hashed_password",
            is_active=False
        )
        mock_user_repo.get_by_email.return_value = user
        
        service = UserAuthService(mock_user_repo, mock_wallet_repo, mock_password_service)
        result = service.authenticate_user("test@example.com", "correct_password")
        
        assert result is None

    def test_change_password_success(self):
        mock_user_repo = Mock()
        mock_wallet_repo = Mock()
        mock_password_service = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="old_hashed_password"
        )
        
        mock_password_service.verify_password.return_value = True
        mock_password_service.validate_password_strength.return_value = {'is_strong': True}
        mock_password_service.hash_password.return_value = "new_hashed_password"
        mock_user_repo.update_user.return_value = user
        
        service = UserAuthService(mock_user_repo, mock_wallet_repo, mock_password_service)
        result = service.change_password(user, "old_password", "new_strong_password")
        
        assert result is True
        mock_password_service.verify_password.assert_called_once_with("old_password", "old_hashed_password")
        mock_password_service.validate_password_strength.assert_called_once_with("new_strong_password")
        mock_password_service.hash_password.assert_called_once_with("new_strong_password")


class TestWalletManagementService:
    
    def test_get_user_wallet(self):
        mock_wallet_repo = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash"
        )
        
        wallet = Wallet(
            id=uuid4(),
            owner_id=user.id,
            balance=Decimal("100.00")
        )
        mock_wallet_repo.get_by_owner_id.return_value = wallet
        
        service = WalletManagementService(mock_wallet_repo)
        result = service.get_user_wallet(user)
        
        assert result == wallet
        mock_wallet_repo.get_by_owner_id.assert_called_once_with(user.id)

    def test_top_up_wallet(self):
        mock_wallet_repo = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash"
        )
        
        wallet = Wallet(
            id=uuid4(),
            owner_id=user.id,
            balance=Decimal("50.00")
        )
        mock_wallet_repo.get_by_owner_id.return_value = wallet
        
        updated_wallet = Wallet(
            id=wallet.id,
            owner_id=user.id,
            balance=Decimal("100.00")
        )
        mock_wallet_repo.update_balance.return_value = updated_wallet
        
        transaction = TopUpTransaction(
            id=uuid4(),
            wallet_id=wallet.id,
            amount=Decimal("50.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("100.00")
        )
        mock_wallet_repo.add_transaction.return_value = transaction
        
        service = WalletManagementService(mock_wallet_repo)
        result = service.top_up_wallet(user, Decimal("50.00"), "Test top up")
        
        assert result.amount == Decimal("50.00")
        mock_wallet_repo.get_by_owner_id.assert_called_once_with(user.id)
        mock_wallet_repo.update_balance.assert_called_once_with(wallet.id, Decimal("100.00"))

    def test_charge_for_task_success(self):
        mock_wallet_repo = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash"
        )
        
        wallet = Wallet(
            id=uuid4(),
            owner_id=user.id,
            balance=Decimal("100.00")
        )
        mock_wallet_repo.get_by_owner_id.return_value = wallet
        
        updated_wallet = Wallet(
            id=wallet.id,
            owner_id=user.id,
            balance=Decimal("75.00")
        )
        mock_wallet_repo.update_balance.return_value = updated_wallet
        
        transaction = SpendTransaction(
            id=uuid4(),
            wallet_id=wallet.id,
            amount=Decimal("25.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("75.00")
        )
        mock_wallet_repo.add_transaction.return_value = transaction
        
        service = WalletManagementService(mock_wallet_repo)
        task_id = uuid4()
        result = service.charge_for_task(user, Decimal("25.00"), task_id)
        
        assert result.amount == Decimal("25.00")
        mock_wallet_repo.get_by_owner_id.assert_called_once_with(user.id)
        mock_wallet_repo.update_balance.assert_called_once_with(wallet.id, Decimal("75.00"))

    def test_charge_for_task_insufficient_funds(self):
        mock_wallet_repo = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash"
        )
        
        wallet = Wallet(
            id=uuid4(),
            owner_id=user.id,
            balance=Decimal("10.00")
        )
        mock_wallet_repo.get_by_owner_id.return_value = wallet
        
        service = WalletManagementService(mock_wallet_repo)
        task_id = uuid4()
        
        with pytest.raises(ValueError, match="Недостаточно средств"):
            service.charge_for_task(user, Decimal("25.00"), task_id)

    def test_check_sufficient_funds(self):
        mock_wallet_repo = Mock()
        
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash"
        )
        
        wallet = Wallet(
            id=uuid4(),
            owner_id=user.id,
            balance=Decimal("100.00")
        )
        mock_wallet_repo.get_by_owner_id.return_value = wallet
        
        service = WalletManagementService(mock_wallet_repo)
        
        assert service.check_sufficient_funds(user, Decimal("50.00")) is True
        assert service.check_sufficient_funds(user, Decimal("150.00")) is False