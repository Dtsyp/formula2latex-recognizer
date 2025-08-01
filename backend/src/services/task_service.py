import base64
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from domain.file import File as DomainFile
from domain.user import User
from infrastructure.messaging import RabbitMQManager
from infrastructure.models import File
from infrastructure.repositories import MLModelRepository, WalletRepository, TaskRepository

logger = logging.getLogger(__name__)


class TaskService:
    """
    Сервис для работы с задачами распознавания формул.
    Инкапсулирует бизнес-логику создания и обработки задач.
    """
    
    def __init__(self, db, messaging: RabbitMQManager):
        self.db = db
        self.messaging = messaging
        self.model_repo = MLModelRepository(db)
        self.wallet_repo = WalletRepository(db)
        self.task_repo = TaskRepository(db)
    
    def create_prediction_task(
        self, 
        user: User, 
        model_id: UUID, 
        file_content: str, 
        filename: str
    ) -> Dict[str, Any]:
        """
        Создает задачу для распознавания формулы.
        
        Args:
            user: Пользователь, создающий задачу
            model_id: ID модели ML для использования
            file_content: Base64 содержимое изображения
            filename: Имя файла
            
        Returns:
            Информация о созданной задаче
            
        Raises:
            ValueError: Если модель не найдена или недостаточно кредитов
            Exception: При других ошибках обработки
        """
        # Валидация модели
        model = self.model_repo.get_by_id(model_id)
        if not model:
            raise ValueError("Model not found")
        
        # Проверка баланса пользователя
        wallet = self.wallet_repo.get_by_owner_id(user.id)
        if wallet.balance < model.credit_cost:
            raise ValueError("Insufficient credits")
        
        # Валидация изображения
        try:
            base64.b64decode(file_content)
        except Exception:
            raise ValueError("Invalid base64 image data")
        
        # Определение типа контента
        content_type = self._determine_content_type(filename)
        
        try:
            # Создание файла в БД
            domain_file = DomainFile(filename, content_type)
            file_model = File(
                path=filename,
                content_type=content_type,
                original_filename=filename
            )
            self.db.add(file_model)
            self.db.commit()
            self.db.refresh(file_model)
            
            # Создание задачи через доменную модель
            task = user.execute_task(domain_file, model)
            
            # Связываем задачу с файлом
            class FileWithId:
                def __init__(self, id, path, content_type):
                    self.id = id
                    self.path = path
                    self.content_type = content_type
            
            task._file = FileWithId(file_model.id, file_model.path, file_model.content_type)
            
            # Сохранение задачи в БД
            self.task_repo.create_task(task)
            
            # Подготовка данных для ML воркера
            task_data = {
                "task_id": str(task.id),
                "user_id": str(user.id),
                "image_data": file_content,
                "filename": filename,
                "model_id": str(model_id)
            }
            
            # Отправка задачи в очередь
            ml_task_id = self.messaging.publish_task(task_data)
            logger.info(f"Task {task.id} published to RabbitMQ as {ml_task_id}")
            
            # Обновление баланса кошелька
            if wallet.transactions:
                self.wallet_repo.add_transaction(wallet.transactions[-1])
            self.wallet_repo.update_balance(wallet.id, wallet.balance)
            
            return {
                "id": task.id,
                "status": "pending",
                "credits_charged": task.credits_charged,
                "created_at": task._timestamp,
                "ml_task_id": ml_task_id
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating prediction task: {e}")
            raise Exception(f"Failed to process task: {str(e)}")
    
    def get_task_result_sync(self, task_id: UUID, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Синхронное получение результата задачи из очереди.
        
        ВАЖНО: Этот метод используется для получения результатов пользователем
        через polling или websocket подключения. Result Processor обновляет 
        задачи в БД асинхронно, но этот метод позволяет получить результат
        немедленно из RabbitMQ очереди.
        
        Args:
            task_id: ID задачи
            timeout: Таймаут ожидания в секундах
            
        Returns:
            Результат задачи или None если таймаут
        """
        result = self.messaging.get_task_result(str(task_id), timeout)
        if result:
            logger.info(f"Retrieved result for task {task_id} from RabbitMQ")
        else:
            logger.warning(f"No result received for task {task_id} within {timeout}s")
        return result
    
    def get_user_tasks(self, user: User):
        """
        Получает все задачи пользователя.
        
        Args:
            user: Пользователь
            
        Returns:
            Список задач пользователя
        """
        return user.get_tasks()
    
    def get_task_by_id(self, user: User, task_id: UUID):
        """
        Получает конкретную задачу пользователя по ID.
        
        Args:
            user: Пользователь
            task_id: ID задачи
            
        Returns:
            Задача или None если не найдена
            
        Raises:
            ValueError: Если задача не найдена
        """
        user_tasks = user.get_tasks()
        task = next((t for t in user_tasks if t.id == task_id), None)
        
        if not task:
            raise ValueError("Task not found")
        
        return task
    
    def _determine_content_type(self, filename: str) -> str:
        """Определяет тип контента по расширению файла"""
        filename_lower = filename.lower()
        if filename_lower.endswith(('.jpg', '.jpeg')):
            return "image/jpeg"
        elif filename_lower.endswith('.gif'):
            return "image/gif"
        else:
            return "image/png"