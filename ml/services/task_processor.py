import logging
import time
from typing import Dict, Any

from interfaces.ml_interfaces import TaskProcessorInterface, MLModelInterface

logger = logging.getLogger(__name__)


class TaskProcessingService(TaskProcessorInterface):
    
    def __init__(self, ml_model: MLModelInterface):
        self._ml_model = ml_model
    
    def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task_data.get('task_id', 'unknown')
        start_time = time.time()
        
        try:
            logger.info(f"Начало обработки задачи {task_id}")
            
            prediction_result = self._ml_model.predict(task_data['image_data'])
            processing_time = time.time() - start_time
            
            result = {
                "task_id": task_id,
                "user_id": task_data.get('user_id'),
                "success": prediction_result['success'],
                "processing_time": processing_time,
                "timestamp": time.time()
            }
            
            if prediction_result['success']:
                result.update({
                    "latex_code": prediction_result['latex_code'],
                    "confidence": prediction_result.get('confidence', 0.0)
                })
                logger.info(f"Задача {task_id} обработана успешно за {processing_time:.2f}с")
            else:
                result.update({
                    "error": prediction_result['error']
                })
                logger.warning(f"Задача {task_id} завершилась с ошибкой: {prediction_result['error']}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Ошибка обработки задачи {task_id}: {str(e)}"
            logger.error(error_msg)
            
            return {
                "task_id": task_id,
                "user_id": task_data.get('user_id'),
                "success": False,
                "error": error_msg,
                "processing_time": processing_time,
                "timestamp": time.time()
            }