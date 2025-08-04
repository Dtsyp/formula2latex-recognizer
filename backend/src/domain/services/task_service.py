from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from decimal import Decimal

from domain.user import User
from domain.task import RecognitionTask
from domain.file import File
from domain.interfaces.repositories import (
    TaskRepositoryInterface, 
    MLModelRepositoryInterface,
    WalletRepositoryInterface
)
from domain.interfaces.services import TaskServiceInterface, WalletServiceInterface
from domain.interfaces.messaging import MessageBrokerInterface
from domain.interfaces.ml_model import ImageValidatorInterface


class TaskManagementService(TaskServiceInterface):
    """
    Доменный сервис для управления задачами распознавания.
    """
    
    def __init__(
        self,
        task_repo: TaskRepositoryInterface,
        model_repo: MLModelRepositoryInterface,
        wallet_service: WalletServiceInterface,
        message_broker: MessageBrokerInterface,
        image_validator: ImageValidatorInterface
    ):
        self._task_repo = task_repo
        self._model_repo = model_repo
        self._wallet_service = wallet_service
        self._message_broker = message_broker
        self._image_validator = image_validator
    
    def create_recognition_task(
        self, 
        user: User, 
        image_data: str, 
        filename: str, 
        model_id: UUID
    ) -> RecognitionTask:
        """
        Создать задачу распознавания формулы.
        """
        # Проверяем что пользователь активен
        if not user.is_active:
            raise ValueError("Пользователь деактивирован")
        
        # Получаем модель
        model = self._model_repo.get_by_id(model_id)
        if not model:
            raise ValueError(f"ML модель с ID {model_id} не найдена")
        
        # Валидируем изображение
        validation_result = self._image_validator.validate_format(image_data)
        if not validation_result['valid']:
            raise ValueError(f"Невалидное изображение: {validation_result['error']}")
        
        size_validation = self._image_validator.validate_size(image_data)
        if not size_validation['valid']:
            raise ValueError(f"Неподходящий размер изображения: {size_validation['error']}")
        
        # Проверяем достаточность средств
        if not self._wallet_service.check_sufficient_funds(user, model.credit_cost):
            raise ValueError("Недостаточно средств для выполнения задачи")
        
        # Создаем файл
        content_type = self._determine_content_type(filename)
        file = File(filename, content_type)
        
        # Создаем задачу
        task = RecognitionTask(
            id=uuid4(),
            user_id=user.id,
            file=file,
            model=model
        )
        
        # Списываем средства (создаем транзакцию)
        self._wallet_service.charge_for_task(user, model.credit_cost, task.id)
        
        # Сохраняем задачу в БД
        self._task_repo.create_task(task)
        
        # Отправляем задачу в очередь для обработки
        task_data = {
            "task_id": str(task.id),
            "user_id": str(user.id),
            "image_data": image_data,
            "filename": filename,
            "model_id": str(model_id)
        }
        
        ml_task_id = self._message_broker.publish_task(task_data)
        
        return task
    
    def get_user_tasks(self, user: User, limit: int = 100) -> List[RecognitionTask]:
        """Получить задачи пользователя"""
        return self._task_repo.get_by_user_id(user.id, limit)
    
    def get_task_by_id(self, user: User, task_id: UUID) -> Optional[RecognitionTask]:
        """
        Получить задачу пользователя по ID.
        
        Проверяет что задача принадлежит пользователю.
        """
        task = self._task_repo.get_by_id(task_id)
        
        if not task:
            return None
        
        # Проверяем что задача принадлежит пользователю (или пользователь - админ)
        if task.user_id != user.id and not user.is_admin():
            return None
        
        return task
    
    def get_task_result_sync(self, task_id: UUID, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Получить результат задачи синхронно из очереди сообщений.
        
        Используется для быстрого получения результатов без ожидания
        обновления в БД через Result Processor.
        """
        return self._message_broker.get_task_result(str(task_id), timeout)
    
    def cancel_task(self, user: User, task_id: UUID) -> bool:
        """
        Отменить задачу (если она еще не начата).
        """
        task = self.get_task_by_id(user, task_id)
        if not task:
            raise ValueError("Задача не найдена")
        
        if task.status != "pending":
            raise ValueError(f"Нельзя отменить задачу в статусе: {task.status}")
        
        # Обновляем статус задачи
        self._task_repo.update_task_status(task_id, "cancelled")
        
        # Возвращаем средства пользователю
        model = self._model_repo.get_by_id(task.model.id)
        if model:
            self._wallet_service.top_up_wallet(
                user, 
                model.credit_cost, 
                f"Возврат средств за отмененную задачу {task_id}"
            )
        
        return True
    
    def get_all_tasks_for_admin(self, limit: int = 100) -> List[RecognitionTask]:
        """
        Получить все задачи в системе (только для администраторов).
        """
        return self._task_repo.get_pending_tasks(limit)
    
    def _determine_content_type(self, filename: str) -> str:
        """Определить тип контента по расширению файла"""
        filename_lower = filename.lower()
        if filename_lower.endswith(('.jpg', '.jpeg')):
            return "image/jpeg"
        elif filename_lower.endswith('.gif'):
            return "image/gif"
        elif filename_lower.endswith('.png'):
            return "image/png"
        else:
            return "image/png"  # По умолчанию