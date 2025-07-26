from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from domain.file import File
from domain.model import MLModel
from domain.task import RecognitionTask
from domain.user import User, Admin
from domain.wallet import Wallet, Transaction, TopUpTransaction, SpendTransaction
from infrastructure.models import (
    FileModel,
    MLModelModel,
    TaskModel,
    TaskStatus,
    TransactionModel,
    TransactionType,
    UserModel,
    UserRole,
    WalletModel,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, email: str, password: str, role: str = "user") -> User:
        password_hash = pwd_context.hash(password)
        
        user_model = UserModel(
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN if role == "admin" else UserRole.USER
        )
        self.db.add(user_model)
        self.db.flush()
        
        wallet_model = WalletModel(owner_id=user_model.id)
        self.db.add(wallet_model)
        self.db.commit()
        
        return self._model_to_domain(user_model)

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        user_model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._model_to_domain(user_model) if user_model else None

    def get_by_email(self, email: str) -> Optional[User]:
        user_model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._model_to_domain(user_model) if user_model else None

    def get_all(self) -> List[User]:
        user_models = self.db.query(UserModel).all()
        return [self._model_to_domain(model) for model in user_models]

    def update_user(self, user: User) -> User:
        user_model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if user_model:
            user_model.email = user.email
            self.db.commit()
        return self._model_to_domain(user_model)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def _model_to_domain(self, user_model: UserModel) -> Optional[User]:
        if not user_model:
            return None
            
        wallet_repo = WalletRepository(self.db)
        wallet = wallet_repo.get_by_owner_id(user_model.id)
        
        if user_model.role == UserRole.ADMIN:
            return Admin(
                id=user_model.id,
                email=user_model.email,
                password_hash=user_model.password_hash,
                wallet=wallet
            )
        else:
            return User(
                id=user_model.id,
                email=user_model.email,
                password_hash=user_model.password_hash,
                wallet=wallet
            )

class WalletRepository:
    """Репозиторий для работы с кошельками."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_owner_id(self, owner_id: UUID) -> Optional[Wallet]:
        wallet_model = self.db.query(WalletModel).filter(WalletModel.owner_id == owner_id).first()
        return self._model_to_domain(wallet_model) if wallet_model else None

    def get_by_id(self, wallet_id: UUID) -> Optional[Wallet]:
        wallet_model = self.db.query(WalletModel).filter(WalletModel.id == wallet_id).first()
        return self._model_to_domain(wallet_model) if wallet_model else None

    def update_balance(self, wallet_id: UUID, new_balance: Decimal) -> None:
        wallet_model = self.db.query(WalletModel).filter(WalletModel.id == wallet_id).first()
        if wallet_model:
            wallet_model.balance = new_balance
            self.db.commit()

    def add_transaction(self, transaction: Transaction) -> None:
        transaction_type = (
            TransactionType.TOP_UP 
            if isinstance(transaction, TopUpTransaction) 
            else TransactionType.SPEND
        )
        transaction_model = TransactionModel(
            wallet_id=transaction.wallet_id,
            type=transaction_type,
            amount=transaction.amount,
            post_balance=transaction.post_balance
        )
        self.db.add(transaction_model)
        self.db.commit()

    def _model_to_domain(self, wallet_model: WalletModel) -> Optional[Wallet]:
        if not wallet_model:
            return None
            
        wallet = Wallet(
            id=wallet_model.id,
            owner_id=wallet_model.owner_id,
            balance=wallet_model.balance
        )
        
        transaction_models = self.db.query(TransactionModel).filter(
            TransactionModel.wallet_id == wallet_model.id
        ).all()
        
        for txn_model in transaction_models:
            if txn_model.type == TransactionType.TOP_UP:
                txn = TopUpTransaction(
                    id=txn_model.id,
                    wallet_id=txn_model.wallet_id,
                    amount=txn_model.amount,
                    timestamp=txn_model.created_at,
                    post_balance=txn_model.post_balance
                )
            else:
                txn = SpendTransaction(
                    id=txn_model.id,
                    wallet_id=txn_model.wallet_id,
                    amount=txn_model.amount,
                    timestamp=txn_model.created_at,
                    post_balance=txn_model.post_balance
                )
            wallet._transactions.append(txn)
        
        return wallet

class TaskRepository:
    """Репозиторий для работы с задачами."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(self, task: RecognitionTask) -> RecognitionTask:
        task_model = TaskModel(
            id=task.id,
            user_id=task._user_id,
            file_id=task._file.path,
            model_id=task._model.id,
            status=TaskStatus.PENDING,
            credits_charged=task.credits_charged
        )
        self.db.add(task_model)
        self.db.commit()
        return task

    def get_by_id(self, task_id: UUID) -> Optional[RecognitionTask]:
        task_model = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        return self._model_to_domain(task_model) if task_model else None

    def get_by_user_id(self, user_id: UUID) -> List[RecognitionTask]:
        task_models = self.db.query(TaskModel).filter(TaskModel.user_id == user_id).all()
        return [self._model_to_domain(model) for model in task_models]

    def update_task_status(
        self, 
        task_id: UUID, 
        status: str, 
        output: Optional[str] = None, 
        error: Optional[str] = None
    ) -> None:
        task_model = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task_model:
            task_model.status = TaskStatus(status)
            if output:
                task_model.output_data = output
            if error:
                task_model.error_message = error
            self.db.commit()

    def _model_to_domain(self, task_model: TaskModel) -> Optional[RecognitionTask]:
        return None

class MLModelRepository:
    """Репозиторий для работы с ML моделями."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_model(self, name: str, credit_cost: Decimal) -> MLModel:
        model_instance = MLModelModel(
            name=name,
            credit_cost=credit_cost
        )
        self.db.add(model_instance)
        self.db.commit()
        return self._model_to_domain(model_instance)

    def get_by_id(self, model_id: UUID) -> Optional[MLModel]:
        model_instance = self.db.query(MLModelModel).filter(MLModelModel.id == model_id).first()
        return self._model_to_domain(model_instance) if model_instance else None

    def get_active_models(self) -> List[MLModel]:
        model_instances = self.db.query(MLModelModel).filter(MLModelModel.is_active == 1).all()
        return [self._model_to_domain(model) for model in model_instances]

    def _model_to_domain(self, model_instance: MLModelModel) -> MLModel:
        class DemoMLModel(MLModel):
            def preprocess(self, file: File):
                return "preprocessed_data"
            
            def predict(self, data):
                return "\\sum_{i=1}^{n} x_i"
        
        return DemoMLModel(
            id=model_instance.id,
            name=model_instance.name,
            credit_cost=model_instance.credit_cost
        )

class FileRepository:
    """Репозиторий для работы с файлами."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_file(
        self, 
        path: str, 
        content_type: str, 
        original_filename: str = None, 
        size: int = None
    ) -> File:
        file_model = FileModel(
            path=path,
            content_type=content_type,
            original_filename=original_filename,
            size=size
        )
        self.db.add(file_model)
        self.db.commit()
        
        return File(path=file_model.path, content_type=file_model.content_type)

    def get_by_id(self, file_id: UUID) -> Optional[File]:
        file_model = self.db.query(FileModel).filter(FileModel.id == file_id).first()
        return File(path=file_model.path, content_type=file_model.content_type) if file_model else None