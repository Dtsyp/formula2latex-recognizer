import logging
from typing import Dict, Any

from interfaces.ml_interfaces import TaskValidatorInterface, MLModelInterface

logger = logging.getLogger(__name__)


class TaskValidationService(TaskValidatorInterface):
    
    def __init__(self, ml_model: MLModelInterface):
        self._ml_model = ml_model
    
    def validate(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            required_fields = ['task_id', 'user_id', 'image_data']
            for field in required_fields:
                if field not in task_data:
                    return {
                        "valid": False,
                        "error": f"Отсутствует обязательное поле: {field}"
                    }
            
            image_validation = self._ml_model.validate_image(task_data['image_data'])
            if not image_validation['valid']:
                return {
                    "valid": False,
                    "error": f"Невалидное изображение: {image_validation['error']}"
                }
            
            return {
                "valid": True,
                "image_info": image_validation,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Ошибка валидации задачи: {e}")
            return {
                "valid": False,
                "error": f"Ошибка валидации: {str(e)}"
            }