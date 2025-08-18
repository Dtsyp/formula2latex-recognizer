from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from domain.interfaces.repositories import (
    UserRepositoryInterface,
    WalletRepositoryInterface, 
    TaskRepositoryInterface,
    MLModelRepositoryInterface
)
from domain.file import File as DomainFile
from domain.model import MLModel as DomainMLModel
from domain.task import RecognitionTask
from domain.user import User as DomainUser, Admin
from domain.wallet import Wallet as DomainWallet, Transaction as DomainTransaction, TopUpTransaction, SpendTransaction
from infrastructure.models import (
    File,
    MLModel,
    Task,
    TaskStatus,
    Transaction,
    TransactionType,
    User,
    UserRole,
    Wallet,
)

class SQLAlchemyUserRepository(UserRepositoryInterface):

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, email: str, password_hash: str, role: str = "user") -> DomainUser:
        user_model = User(
            email=email,
            password=password_hash,
            role=UserRole.ADMIN if role == "admin" else UserRole.USER
        )
        self.db.add(user_model)
        self.db.flush()
        
        wallet_model = Wallet(owner_id=user_model.id)
        self.db.add(wallet_model)
        self.db.commit()
        
        return self._model_to_domain(user_model)

    def get_by_id(self, user_id: UUID) -> Optional[DomainUser]:
        user_model = self.db.query(User).filter(User.id == user_id).first()
        return self._model_to_domain(user_model) if user_model else None

    def get_by_email(self, email: str) -> Optional[DomainUser]:
        user_model = self.db.query(User).filter(User.email == email).first()
        return self._model_to_domain(user_model) if user_model else None

    def update_user(self, user: DomainUser) -> DomainUser:
        user_model = self.db.query(User).filter(User.id == user.id).first()
        if not user_model:
            raise ValueError(f"User with id {user.id} not found")
            
        user_model.email = user.email
        user_model.password = user.password_hash
        user_model.role = UserRole.ADMIN if user.role == "admin" else UserRole.USER
        user_model.is_active = user.is_active
        self.db.commit()
        
        return self._model_to_domain(user_model)
    
    def delete_user(self, user_id: UUID) -> bool:
        user_model = self.db.query(User).filter(User.id == user_id).first()
        if not user_model:
            return False
            
        self.db.delete(user_model)
        self.db.commit()
        return True

    def _model_to_domain(self, user_model: User) -> Optional[DomainUser]:
        if not user_model:
            return None
            
        if user_model.role == UserRole.ADMIN:
            return Admin(
                id=user_model.id,
                email=user_model.email,
                password_hash=user_model.password,
                role="admin",
                is_active=user_model.is_active
            )
        else:
            return DomainUser(
                id=user_model.id,
                email=user_model.email,
                password_hash=user_model.password,
                role="user",
                is_active=user_model.is_active
            )

class SQLAlchemyWalletRepository(WalletRepositoryInterface):

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_owner_id(self, owner_id: UUID) -> Optional[DomainWallet]:
        wallet_model = self.db.query(Wallet).filter(Wallet.owner_id == owner_id).order_by(Wallet.created_at.desc()).first()
        return self._model_to_domain(wallet_model) if wallet_model else None

    def create_wallet(self, owner_id: UUID, initial_balance: Decimal = Decimal("0")) -> DomainWallet:
        wallet_model = Wallet(
            owner_id=owner_id,
            balance=initial_balance
        )
        self.db.add(wallet_model)
        self.db.commit()
        
        return self._model_to_domain(wallet_model)
    
    def update_balance(self, wallet_id: UUID, new_balance: Decimal) -> DomainWallet:
        wallet_model = self.db.query(Wallet).filter(Wallet.id == wallet_id).first()
        if not wallet_model:
            raise ValueError(f"Wallet with id {wallet_id} not found")
            
        wallet_model.balance = new_balance
        self.db.commit()
        
        return self._model_to_domain(wallet_model)

    def add_transaction(self, transaction: DomainTransaction) -> DomainTransaction:
        transaction_type = (
            TransactionType.TOP_UP 
            if isinstance(transaction, TopUpTransaction) 
            else TransactionType.SPEND
        )
        transaction_model = Transaction(
            wallet_id=transaction.wallet_id,
            type=transaction_type,
            amount=transaction.amount,
            post_balance=transaction.post_balance
        )
        self.db.add(transaction_model)
        self.db.commit()
        
        return transaction
    
    def get_transactions(self, wallet_id: UUID, limit: int = 100) -> List[DomainTransaction]:
        transaction_models = self.db.query(Transaction).filter(
            Transaction.wallet_id == wallet_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()
        
        transactions = []
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
            transactions.append(txn)
        
        return transactions

    def _model_to_domain(self, wallet_model: Wallet) -> Optional[DomainWallet]:
        if not wallet_model:
            return None
            
        wallet = DomainWallet(
            id=wallet_model.id,
            owner_id=wallet_model.owner_id,
            balance=wallet_model.balance
        )
        
        transaction_models = self.db.query(Transaction).filter(
            Transaction.wallet_id == wallet_model.id
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

class SQLAlchemyTaskRepository(TaskRepositoryInterface):

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(self, task: RecognitionTask) -> RecognitionTask:
        task_model = Task(
            id=task.id,
            user_id=task._user_id,
            file_id=task._file.id,  # Используем UUID вместо path
            model_id=task._model.id,
            status=TaskStatus.PENDING,
            credits_charged=task.credits_charged
        )
        self.db.add(task_model)
        self.db.commit()
        return task

    def get_by_id(self, task_id: UUID) -> Optional[RecognitionTask]:
        task_model = self.db.query(Task).filter(Task.id == task_id).first()
        return self._model_to_domain(task_model) if task_model else None

    def get_by_user_id(self, user_id: UUID) -> List[RecognitionTask]:
        task_models = self.db.query(Task).filter(Task.user_id == user_id).all()
        return [self._model_to_domain(model) for model in task_models]

    def update_task_status(
        self, 
        task_id: UUID, 
        status: str, 
        output: str = None, 
        error: str = None
    ) -> RecognitionTask:
        task_model = self.db.query(Task).filter(Task.id == task_id).first()
        if not task_model:
            raise ValueError(f"Task with id {task_id} not found")
            
        task_model.status = TaskStatus(status)
        if output:
            task_model.output_data = output
        if error:
            task_model.error_message = error
        self.db.commit()
        
        return self._model_to_domain(task_model)
    
    def get_pending_tasks(self, limit: int = 100) -> List[RecognitionTask]:
        task_models = self.db.query(Task).filter(
            Task.status == TaskStatus.PENDING
        ).limit(limit).all()
        
        return [self._model_to_domain(model) for model in task_models if model]

    def _model_to_domain(self, task_model: Task) -> Optional[RecognitionTask]:
        return None

class SQLAlchemyMLModelRepository(MLModelRepositoryInterface):

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_model(self, name: str, credit_cost: Decimal, is_active: bool = True) -> DomainMLModel:
        model_instance = MLModel(
            name=name,
            credit_cost=credit_cost,
            is_active=is_active
        )
        self.db.add(model_instance)
        self.db.commit()
        return self._model_to_domain(model_instance)

    def get_by_id(self, model_id: UUID) -> Optional[DomainMLModel]:
        model_instance = self.db.query(MLModel).filter(MLModel.id == model_id).first()
        return self._model_to_domain(model_instance) if model_instance else None

    def get_all_active(self) -> List[DomainMLModel]:
        model_instances = self.db.query(MLModel).filter(MLModel.is_active == True).all()
        return [self._model_to_domain(model) for model in model_instances]
    
    def update_model(self, model: DomainMLModel) -> DomainMLModel:
        model_instance = self.db.query(MLModel).filter(MLModel.id == model.id).first()
        if not model_instance:
            raise ValueError(f"Model with id {model.id} not found")
            
        model_instance.name = model.name
        model_instance.credit_cost = model.credit_cost
        self.db.commit()
        
        return self._model_to_domain(model_instance)
    
    def deactivate_model(self, model_id: UUID) -> bool:
        model_instance = self.db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model_instance:
            return False
            
        model_instance.is_active = False
        self.db.commit()
        return True

    def _model_to_domain(self, model_instance: MLModel) -> DomainMLModel:
        class DemoMLModel(DomainMLModel):
            def preprocess(self, file: DomainFile):
                return "preprocessed_data"
            
            def predict(self, data):
                return "\\sum_{i=1}^{n} x_i"
        
        return DemoMLModel(
            id=model_instance.id,
            name=model_instance.name,
            credit_cost=model_instance.credit_cost
        )

class FileRepository:

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_file(
        self, 
        path: str, 
        content_type: str, 
        original_filename: str = None, 
        size: int = None
    ) -> DomainFile:
        file_model = File(
            path=path,
            content_type=content_type,
            original_filename=original_filename,
            size=size
        )
        self.db.add(file_model)
        self.db.commit()
        
        return DomainFile(path=file_model.path, content_type=file_model.content_type)

    def get_by_id(self, file_id: UUID) -> Optional[DomainFile]:
        file_model = self.db.query(File).filter(File.id == file_id).first()
        return DomainFile(path=file_model.path, content_type=file_model.content_type) if file_model else None