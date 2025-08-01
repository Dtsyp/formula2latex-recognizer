from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal


class MLModelInterface(ABC):
    """
    Абстракция для ML модели.
    Определена в доменном слое - все реализации будут от неё зависеть.
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """Получить название модели"""
        pass
    
    @abstractmethod
    def get_credit_cost(self) -> Decimal:
        """Получить стоимость использования модели в кредитах"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверить доступность модели для использования"""
        pass
    
    @abstractmethod
    def validate_image(self, image_data: str) -> Dict[str, Any]:
        """
        Валидировать входное изображение.
        
        Args:
            image_data: Base64 строка изображения
            
        Returns:
            dict с ключами:
            - valid: bool - валидно ли изображение
            - error: str - описание ошибки если не валидно
            - width: int - ширина изображения
            - height: int - высота изображения
            - format: str - формат изображения
        """
        pass
    
    @abstractmethod
    def predict(self, image_data: str) -> Dict[str, Any]:
        """
        Выполнить предсказание для изображения.
        
        Args:
            image_data: Base64 строка изображения
            
        Returns:
            dict с ключами:
            - success: bool - успешно ли выполнено предсказание
            - latex_code: str - LaTeX код формулы (если успешно)
            - confidence: float - уверенность модели (0.0-1.0)
            - error: str - описание ошибки (если не успешно)
            - processing_time: float - время обработки в секундах
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Получить информацию о модели.
        
        Returns:
            dict с метаданными модели (версия, размер, точность и т.д.)
        """
        pass


class MLModelFactoryInterface(ABC):
    """
    Абстракция для фабрики ML моделей.
    Позволяет создавать разные типы моделей без жесткой привязки к конкретным реализациям.
    """
    
    @abstractmethod
    def create_model(self, model_type: str, **kwargs) -> MLModelInterface:
        """
        Создать ML модель по типу.
        
        Args:
            model_type: Тип модели (например, "trocr", "custom", "demo")
            **kwargs: Дополнительные параметры для конкретной модели
            
        Returns:
            Экземпляр ML модели
            
        Raises:
            ValueError: Если тип модели не поддерживается
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> list[str]:
        """Получить список поддерживаемых типов моделей"""
        pass
    
    @abstractmethod
    def register_model_type(self, model_type: str, model_class: type) -> None:
        """
        Зарегистрировать новый тип модели.
        
        Args:
            model_type: Название типа модели
            model_class: Класс модели, реализующий MLModelInterface
        """
        pass


class ImageValidatorInterface(ABC):
    """
    Абстракция для валидации изображений.
    Отделена от ML модели для лучшего разделения ответственностей.
    """
    
    @abstractmethod
    def validate_format(self, image_data: str) -> Dict[str, Any]:
        """Валидировать формат изображения"""
        pass
    
    @abstractmethod
    def validate_size(self, image_data: str, max_width: int = 2048, max_height: int = 2048) -> Dict[str, Any]:
        """Валидировать размер изображения"""
        pass
    
    @abstractmethod
    def validate_content(self, image_data: str) -> Dict[str, Any]:
        """Валидировать содержимое изображения (например, наличие формул)"""
        pass
    
    @abstractmethod
    def get_image_info(self, image_data: str) -> Dict[str, Any]:
        """Получить информацию об изображении"""
        pass


class ModelPerformanceMonitorInterface(ABC):
    """
    Абстракция для мониторинга производительности моделей.
    """
    
    @abstractmethod
    def record_prediction(self, model_name: str, processing_time: float, confidence: float, success: bool) -> None:
        """Записать метрики предсказания"""
        pass
    
    @abstractmethod
    def get_model_stats(self, model_name: str, time_period_hours: int = 24) -> Dict[str, Any]:
        """Получить статистику модели за период"""
        pass
    
    @abstractmethod
    def get_average_processing_time(self, model_name: str) -> float:
        """Получить среднее время обработки"""
        pass
    
    @abstractmethod
    def get_success_rate(self, model_name: str) -> float:
        """Получить процент успешных предсказаний"""
        pass