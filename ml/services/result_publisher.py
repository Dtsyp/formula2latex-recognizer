import json
import logging
import time
from typing import Dict, Any

from interfaces.ml_interfaces import ResultPublisherInterface

logger = logging.getLogger(__name__)


class ResultPublishingService(ResultPublisherInterface):
    
    def __init__(self, rabbitmq_manager):
        self._rabbitmq_manager = rabbitmq_manager
    
    def publish_success(self, result_data: Dict[str, Any]) -> None:
        try:
            self._rabbitmq_manager.publish_result(result_data)
            logger.info(f"Результат задачи {result_data.get('task_id')} опубликован")
        except Exception as e:
            logger.error(f"Ошибка публикации результата: {e}")
            raise
    
    def publish_error(self, task_data: Dict[str, Any], error: str) -> None:
        try:
            error_result = {
                "task_id": task_data.get('task_id'),
                "user_id": task_data.get('user_id'),
                "success": False,
                "error": error,
                "timestamp": time.time()
            }
            
            self._rabbitmq_manager.publish_result(error_result)
            logger.info(f"Ошибка задачи {task_data.get('task_id')} опубликована")
        except Exception as e:
            logger.error(f"Ошибка публикации ошибки: {e}")
            raise