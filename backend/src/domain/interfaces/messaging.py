from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable


class MessageBrokerInterface(ABC):
    """
    Абстракция для системы обмена сообщениями.
    Определена в доменном слое - инфраструктура будет от неё зависеть.
    """
    
    @abstractmethod
    def connect(self) -> None:
        """Установить соединение с брокером сообщений"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Закрыть соединение с брокером"""
        pass
    
    @abstractmethod
    def publish_task(self, task_data: Dict[str, Any]) -> str:
        """
        Опубликовать задачу для обработки ML воркерами.
        
        Args:
            task_data: Данные задачи для обработки
            
        Returns:
            ID опубликованной задачи в очереди
        """
        pass
    
    @abstractmethod
    def publish_result(self, result_data: Dict[str, Any]) -> None:
        """
        Опубликовать результат обработки задачи.
        
        Args:
            result_data: Результат обработки задачи
        """
        pass
    
    @abstractmethod
    def get_task_result(self, task_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Получить результат задачи синхронно (с ожиданием).
        
        Args:
            task_id: ID задачи
            timeout: Максимальное время ожидания в секундах
            
        Returns:
            Результат задачи или None если таймаут
        """
        pass
    
    @abstractmethod
    def subscribe_to_tasks(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Подписаться на получение задач (для ML воркеров).
        
        Args:
            callback: Функция для обработки полученных задач
        """
        pass
    
    @abstractmethod
    def subscribe_to_results(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Подписаться на получение результатов (для result processor).
        
        Args:
            callback: Функция для обработки полученных результатов
        """
        pass
    
    @abstractmethod
    def ack_message(self, delivery_tag: str) -> None:
        """
        Подтвердить получение и обработку сообщения.
        
        Args:
            delivery_tag: Тег сообщения для подтверждения
        """
        pass
    
    @abstractmethod
    def reject_message(self, delivery_tag: str, requeue: bool = False) -> None:
        """
        Отклонить сообщение.
        
        Args:
            delivery_tag: Тег сообщения для отклонения
            requeue: Вернуть ли сообщение в очередь
        """
        pass


class TaskQueueInterface(ABC):
    """
    Абстракция для очереди задач.
    Упрощенный интерфейс для случаев когда не нужна полная функциональность брокера.
    """
    
    @abstractmethod
    def enqueue_task(self, task_data: Dict[str, Any]) -> str:
        """Добавить задачу в очередь"""
        pass
    
    @abstractmethod
    def dequeue_task(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Извлечь задачу из очереди"""
        pass
    
    @abstractmethod
    def get_queue_size(self) -> int:
        """Получить размер очереди"""
        pass


class ResultStoreInterface(ABC):
    """
    Абстракция для хранения результатов задач.
    """
    
    @abstractmethod
    def store_result(self, task_id: str, result_data: Dict[str, Any]) -> None:
        """Сохранить результат задачи"""
        pass
    
    @abstractmethod
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получить результат задачи"""
        pass
    
    @abstractmethod
    def remove_result(self, task_id: str) -> bool:
        """Удалить результат задачи"""
        pass
    
    @abstractmethod
    def cleanup_old_results(self, max_age_seconds: int) -> int:
        """Очистить старые результаты"""
        pass