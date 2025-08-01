from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

# Импорты доменных сущностей - правильное направление зависимостей
from domain.user import User
from domain.wallet import Wallet, Transaction
from domain.task import RecognitionTask
from domain.model import MLModel


class UserRepositoryInterface(ABC):
    """
    Абстракция для работы с пользователями.
    Определена в доменном слое - инфраструктура будет от неё зависеть.
    """
    
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получить пользователя по ID"""
        pass
    
    @abstractmethod  
    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        pass
    
    @abstractmethod
    def create_user(self, email: str, password_hash: str, role: str = "user") -> User:
        """Создать нового пользователя"""
        pass
    
    @abstractmethod
    def update_user(self, user: User) -> User:
        """Обновить данные пользователя"""
        pass
    
    @abstractmethod
    def delete_user(self, user_id: UUID) -> bool:
        """Удалить пользователя"""
        pass


class WalletRepositoryInterface(ABC):
    """
    Абстракция для работы с кошельками пользователей.
    """
    
    @abstractmethod
    def get_by_owner_id(self, owner_id: UUID) -> Optional[Wallet]:
        """Получить кошелек пользователя"""
        pass
    
    @abstractmethod
    def create_wallet(self, owner_id: UUID, initial_balance: Decimal = Decimal("0")) -> Wallet:
        """Создать кошелек для пользователя"""
        pass
    
    @abstractmethod
    def update_balance(self, wallet_id: UUID, new_balance: Decimal) -> Wallet:
        """Обновить баланс кошелька"""
        pass
    
    @abstractmethod
    def add_transaction(self, transaction: Transaction) -> Transaction:
        """Добавить транзакцию"""
        pass
    
    @abstractmethod
    def get_transactions(self, wallet_id: UUID, limit: int = 100) -> List[Transaction]:
        """Получить историю транзакций"""
        pass


class TaskRepositoryInterface(ABC):
    """
    Абстракция для работы с задачами распознавания.
    """
    
    @abstractmethod
    def create_task(self, task: RecognitionTask) -> RecognitionTask:
        """Создать новую задачу"""
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: UUID) -> Optional[RecognitionTask]:
        """Получить задачу по ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: UUID, limit: int = 100) -> List[RecognitionTask]:
        """Получить задачи пользователя"""
        pass
    
    @abstractmethod
    def update_task_status(self, task_id: UUID, status: str, output: str = None, error: str = None) -> RecognitionTask:
        """Обновить статус задачи"""
        pass
    
    @abstractmethod
    def get_pending_tasks(self, limit: int = 100) -> List[RecognitionTask]:
        """Получить задачи в ожидании обработки"""
        pass


class MLModelRepositoryInterface(ABC):
    """
    Абстракция для работы с ML моделями.
    """
    
    @abstractmethod
    def get_by_id(self, model_id: UUID) -> Optional[MLModel]:
        """Получить модель по ID"""
        pass
    
    @abstractmethod
    def get_all_active(self) -> List[MLModel]:
        """Получить все активные модели"""
        pass
    
    @abstractmethod
    def create_model(self, name: str, credit_cost: Decimal, is_active: bool = True) -> MLModel:
        """Создать новую модель"""
        pass
    
    @abstractmethod
    def update_model(self, model: MLModel) -> MLModel:
        """Обновить модель"""
        pass
    
    @abstractmethod
    def deactivate_model(self, model_id: UUID) -> bool:
        """Деактивировать модель"""
        pass