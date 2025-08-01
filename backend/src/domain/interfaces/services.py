from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal
from domain.user import User
from domain.task import RecognitionTask
from domain.wallet import Wallet, Transaction


class UserServiceInterface(ABC):
    """
    Абстракция для пользовательских сервисов.
    Инкапсулирует бизнес-логику работы с пользователями.
    """
    
    @abstractmethod
    def register_user(self, email: str, password: str) -> User:
        """
        Зарегистрировать нового пользователя.
        
        Args:
            email: Email пользователя
            password: Пароль в открытом виде
            
        Returns:
            Созданный пользователь
            
        Raises:
            ValueError: Если email уже занят или данные невалидны
        """
        pass
    
    @abstractmethod
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Аутентифицировать пользователя.
        
        Args:
            email: Email пользователя
            password: Пароль в открытом виде
            
        Returns:
            Пользователь если аутентификация успешна, иначе None
        """
        pass
    
    @abstractmethod
    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """
        Изменить пароль пользователя.
        
        Args:
            user: Пользователь
            old_password: Старый пароль
            new_password: Новый пароль
            
        Returns:
            True если пароль изменен успешно
        """
        pass
    
    @abstractmethod
    def change_email(self, user: User, new_email: str) -> User:
        """
        Изменить email пользователя.
        
        Args:
            user: Пользователь
            new_email: Новый email
            
        Returns:
            Обновленный пользователь
            
        Raises:
            ValueError: Если email уже занят
        """
        pass


class WalletServiceInterface(ABC):
    """
    Абстракция для сервисов работы с кошельками.
    """
    
    @abstractmethod
    def get_user_wallet(self, user: User) -> Wallet:
        """Получить кошелек пользователя"""
        pass
    
    @abstractmethod
    def top_up_wallet(self, user: User, amount: Decimal, description: str = "Пополнение") -> Transaction:
        """
        Пополнить кошелек пользователя.
        
        Args:
            user: Пользователь
            amount: Сумма пополнения
            description: Описание транзакции
            
        Returns:
            Созданная транзакция
            
        Raises:
            ValueError: Если сумма некорректна
        """
        pass
    
    @abstractmethod
    def charge_for_task(self, user: User, amount: Decimal, task_id: UUID) -> Transaction:
        """
        Списать средства за выполнение задачи.
        
        Args:
            user: Пользователь
            amount: Сумма к списанию
            task_id: ID задачи
            
        Returns:
            Созданная транзакция
            
        Raises:
            ValueError: Если недостаточно средств
        """
        pass
    
    @abstractmethod
    def get_transaction_history(self, user: User, limit: int = 100) -> List[Transaction]:
        """Получить историю транзакций пользователя"""
        pass
    
    @abstractmethod
    def check_sufficient_funds(self, user: User, required_amount: Decimal) -> bool:
        """Проверить достаточность средств"""
        pass


class TaskServiceInterface(ABC):
    """
    Абстракция для сервисов работы с задачами.
    """
    
    @abstractmethod
    def create_recognition_task(
        self, 
        user: User, 
        image_data: str, 
        filename: str, 
        model_id: UUID
    ) -> RecognitionTask:
        """
        Создать задачу распознавания формулы.
        
        Args:
            user: Пользователь, создающий задачу
            image_data: Base64 изображение
            filename: Имя файла
            model_id: ID модели для обработки
            
        Returns:
            Созданная задача
            
        Raises:
            ValueError: Если данные невалидны или недостаточно средств
        """
        pass
    
    @abstractmethod
    def get_user_tasks(self, user: User, limit: int = 100) -> List[RecognitionTask]:
        """Получить задачи пользователя"""
        pass
    
    @abstractmethod
    def get_task_by_id(self, user: User, task_id: UUID) -> Optional[RecognitionTask]:
        """Получить задачу пользователя по ID"""
        pass
    
    @abstractmethod
    def get_task_result_sync(self, task_id: UUID, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Получить результат задачи синхронно из очереди"""
        pass
    
    @abstractmethod
    def cancel_task(self, user: User, task_id: UUID) -> bool:
        """Отменить задачу (если возможно)"""
        pass


class NotificationServiceInterface(ABC):
    """
    Абстракция для сервиса уведомлений.
    """
    
    @abstractmethod
    def notify_task_completed(self, user: User, task: RecognitionTask, result: Dict[str, Any]) -> None:
        """Уведомить о завершении задачи"""
        pass
    
    @abstractmethod
    def notify_task_failed(self, user: User, task: RecognitionTask, error: str) -> None:
        """Уведомить об ошибке в задаче"""
        pass
    
    @abstractmethod
    def notify_low_balance(self, user: User, current_balance: Decimal) -> None:
        """Уведомить о низком балансе"""
        pass


class PasswordServiceInterface(ABC):
    """
    Абстракция для работы с паролями.
    """
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Хешировать пароль"""
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        """Проверить пароль"""
        pass
    
    @abstractmethod
    def generate_random_password(self, length: int = 12) -> str:
        """Сгенерировать случайный пароль"""
        pass
    
    @abstractmethod
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Проверить силу пароля.
        
        Returns:
            dict с ключами: is_strong (bool), issues (list[str])
        """
        pass


class MessagingServiceInterface(ABC):
    """
    Абстракция для сервиса обмена сообщениями.
    
    Следует принципам SOLID:
    - SRP: Единственная ответственность - обмен сообщениями
    - ISP: Интерфейс содержит только необходимые методы
    - DIP: Определен в доменном слое, инфраструктура от него зависит
    """
    
    @abstractmethod
    def send_task(self, task_data: Dict[str, Any]) -> bool:
        """
        Отправить задачу в очередь для обработки ML воркерами.
        
        Args:
            task_data: Данные задачи (task_id, user_id, image_data, etc.)
            
        Returns:
            True если задача отправлена успешно
        """
        pass
    
    @abstractmethod
    def receive_result(self, task_id: str) -> Dict[str, Any]:
        """
        Получить результат обработки задачи.
        
        Args:
            task_id: ID задачи
            
        Returns:
            Результат обработки или статус ожидания
        """
        pass
    
    @abstractmethod
    def publish_notification(self, user_id: str, message: str) -> bool:
        """
        Отправить уведомление пользователю.
        
        Args:
            user_id: ID пользователя
            message: Текст уведомления
            
        Returns:
            True если уведомление отправлено успешно
        """
        pass