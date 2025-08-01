from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class TaskValidatorInterface(ABC):
    
    @abstractmethod
    def validate(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


class TaskProcessorInterface(ABC):
    
    @abstractmethod
    def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


class ResultPublisherInterface(ABC):
    
    @abstractmethod
    def publish_success(self, result_data: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    def publish_error(self, task_data: Dict[str, Any], error: str) -> None:
        pass


class MLModelInterface(ABC):
    
    @abstractmethod
    def validate_image(self, image_data: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def predict(self, image_data: str) -> Dict[str, Any]:
        pass


class MessageAcknowledgerInterface(ABC):
    
    @abstractmethod
    def ack(self, delivery_tag: str) -> None:
        pass
    
    @abstractmethod
    def reject(self, delivery_tag: str) -> None:
        pass