from decimal import Decimal
from uuid import uuid4
import pytest
import datetime

from domain.user import User, Admin
from domain.wallet import Wallet, TopUpTransaction, SpendTransaction


class TestUser:
    
    def test_create_user(self):
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashedpassword123",
            role="user",
            is_active=True
        )
        
        assert user.email == "test@example.com"
        assert user.password_hash == "hashedpassword123"
        assert user.role == "user"
        assert user.is_active is True

    def test_user_is_admin(self):
        admin_user = User(
            id=uuid4(),
            email="admin@example.com", 
            password_hash="hashedpassword123",
            role="admin"
        )
        
        regular_user = User(
            id=uuid4(),
            email="user@example.com",
            password_hash="hashedpassword123", 
            role="user"
        )
        
        assert admin_user.is_admin() is True
        assert regular_user.is_admin() is False

    def test_user_email_validation(self):
        with pytest.raises(ValueError, match="Некорректный email"):
            User(
                id=uuid4(),
                email="invalid-email",
                password_hash="hashedpassword123"
            )

    def test_user_role_validation(self):
        with pytest.raises(ValueError, match="Недопустимая роль"):
            User(
                id=uuid4(),
                email="test@example.com",
                password_hash="hashedpassword123",
                role="invalid_role"
            )


class TestAdmin:
    
    def test_create_admin(self):
        admin = Admin(
            id=uuid4(),
            email="admin@example.com",
            password_hash="hashedpassword123"
        )
        
        assert admin.role == "admin"
        assert admin.is_admin() is True
        assert isinstance(admin, User)


class TestWallet:
    
    def test_create_wallet(self):
        wallet = Wallet(
            id=uuid4(),
            owner_id=uuid4(),
            balance=Decimal("100.00")
        )
        
        assert wallet.balance == Decimal("100.00")
        assert len(wallet.transactions) == 0

    def test_wallet_add_transaction(self):
        wallet_id = uuid4()
        wallet = Wallet(
            id=wallet_id,
            owner_id=uuid4(),
            balance=Decimal("0")
        )
        
        transaction = wallet.top_up(Decimal("50.00"))
        
        assert len(wallet.transactions) == 1
        assert wallet.transactions[0].amount == Decimal("50.00")
        assert wallet.balance == Decimal("50.00")

    def test_wallet_transactions(self):
        wallet = Wallet(
            id=uuid4(),
            owner_id=uuid4(),
            balance=Decimal("100.00")
        )
        
        spend_transaction = wallet.spend(Decimal("25.00"))
        assert wallet.balance == Decimal("75.00")
        assert spend_transaction.amount == Decimal("25.00")
        
        topup_transaction = wallet.top_up(Decimal("50.00"))
        assert wallet.balance == Decimal("125.00")
        assert topup_transaction.amount == Decimal("50.00")

    def test_wallet_insufficient_funds(self):
        wallet = Wallet(
            id=uuid4(),
            owner_id=uuid4(),
            balance=Decimal("10.00")
        )
        
        with pytest.raises(RuntimeError, match="Недостаточно средств"):
            wallet.spend(Decimal("50.00"))


class TestTransactions:
    
    def test_create_topup_transaction(self):
        transaction = TopUpTransaction(
            id=uuid4(),
            wallet_id=uuid4(),
            amount=Decimal("50.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("150.00")
        )
        
        assert transaction.amount == Decimal("50.00")
        assert transaction.post_balance == Decimal("150.00")
        assert isinstance(transaction, TopUpTransaction)

    def test_create_spend_transaction(self):
        transaction = SpendTransaction(
            id=uuid4(),
            wallet_id=uuid4(),
            amount=Decimal("25.00"),
            timestamp=datetime.datetime.utcnow(),
            post_balance=Decimal("75.00")
        )
        
        assert transaction.amount == Decimal("25.00")
        assert transaction.post_balance == Decimal("75.00")
        assert isinstance(transaction, SpendTransaction)