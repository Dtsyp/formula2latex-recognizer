from decimal import Decimal
from uuid import uuid4
import pytest

from domain.user import User, Admin
from domain.wallet import Wallet, Transaction, TransactionType
from domain.model import MLModel
from domain.file import File
from domain.task import RecognitionTask


class TestUser:
    
    def test_create_user(self):
        user = User(
            id=uuid4(),
            email="test@example.com",
            password="hashedpassword"
        )
        
        assert user.email == "test@example.com"
        assert user.password == "hashedpassword"
        assert user.role == "user"
        assert len(user.get_tasks()) == 0

    def test_user_password_validation(self):
        with pytest.raises(ValueError, match="Пароль должен быть не менее 8 символов"):
            User(
                id=uuid4(),
                email="test@example.com",
                password="short"
            )

    def test_user_email_validation(self):
        with pytest.raises(ValueError, match="Некорректный email"):
            User(
                id=uuid4(),
                email="invalid-email",
                password="password123"
            )


class TestAdmin:
    
    def test_create_admin(self):
        admin = Admin(
            id=uuid4(),
            email="admin@example.com", 
            password="password123"
        )
        
        assert admin.role == "admin"
        assert isinstance(admin, User)

    def test_admin_top_up_user(self):
        admin = Admin(
            id=uuid4(),
            email="admin@example.com",
            password="password123"
        )
        
        user = User(
            id=uuid4(),
            email="user@example.com",
            password="password123"
        )
        
        user._wallet = Wallet(id=uuid4(), owner_id=user.id, balance=Decimal("0"))
        
        transaction = admin.top_up_user(user, Decimal("50.00"))
        
        assert transaction.amount == Decimal("50.00")
        assert transaction.type == TransactionType.TOP_UP
        assert user._wallet.balance == Decimal("50.00")


class TestWallet:
    
    def test_create_wallet(self):
        wallet = Wallet(
            id=uuid4(),
            owner_id=uuid4(),
            balance=Decimal("100.00")
        )
        
        assert wallet.balance == Decimal("100.00")
        assert len(wallet.transactions) == 0

    def test_wallet_top_up(self):
        wallet = Wallet(
            id=uuid4(),
            owner_id=uuid4(),
            balance=Decimal("0")
        )
        
        transaction = wallet.top_up(Decimal("50.00"))
        
        assert wallet.balance == Decimal("50.00")
        assert transaction.amount == Decimal("50.00")
        assert transaction.type == TransactionType.TOP_UP
        assert len(wallet.transactions) == 1

    def test_wallet_spend(self):
        wallet = Wallet(
            id=uuid4(),
            owner_id=uuid4(),
            balance=Decimal("100.00")
        )
        
        transaction = wallet.spend(Decimal("25.00"))
        
        assert wallet.balance == Decimal("75.00")
        assert transaction.amount == Decimal("25.00")
        assert transaction.type == TransactionType.SPEND

    def test_wallet_insufficient_funds(self):
        wallet = Wallet(
            id=uuid4(),
            owner_id=uuid4(),
            balance=Decimal("10.00")
        )
        
        with pytest.raises(RuntimeError, match="Недостаточно средств"):
            wallet.spend(Decimal("50.00"))


class TestMLModel:
    
    def test_create_model(self):
        model = MLModel(
            id=uuid4(),
            name="Test Model",
            credit_cost=Decimal("5.00")
        )
        
        assert model.name == "Test Model"
        assert model.credit_cost == Decimal("5.00")
        assert model.is_active is True


class TestFile:
    
    def test_create_file(self):
        file = File(
            path="test.png",
            content_type="image/png"
        )
        
        assert file.path == "test.png"
        assert file.content_type == "image/png"

    def test_file_validation(self):
        with pytest.raises(ValueError, match="Неподдерживаемый тип файла"):
            File(
                path="test.txt",
                content_type="text/plain"
            )


class TestRecognitionTask:
    
    def test_create_task(self):
        user_id = uuid4()
        file = File("test.png", "image/png")
        model = MLModel(
            id=uuid4(),
            name="Test Model",
            credit_cost=Decimal("2.50")
        )
        
        task = RecognitionTask(
            id=uuid4(),
            user_id=user_id,
            file=file,
            model=model
        )
        
        assert task.user_id == user_id
        assert task.file == file
        assert task.model == model
        assert task.credits_charged == Decimal("2.50")
        assert task.status == "pending"

    def test_task_execution(self):
        user_id = uuid4()
        file = File("test.png", "image/png")
        model = MLModel(
            id=uuid4(),
            name="Test Model", 
            credit_cost=Decimal("2.50")
        )
        
        task = RecognitionTask(
            id=uuid4(),
            user_id=user_id,
            file=file,
            model=model
        )
        
        task.execute()
        
        assert task.status == "completed"
        assert task.output == "x^2 + y^2 = r^2"