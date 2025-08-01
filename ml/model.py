"""
ML модель для распознавания математических формул
Использует TrOCR (Transformer-based Optical Character Recognition) для конвертации изображений в LaTeX
"""

import io
import base64
from typing import Optional, Dict, Any
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import logging

logger = logging.getLogger(__name__)


class Formula2LaTeXModel:
    """Модель для распознавания формул и конвертации в LaTeX"""
    
    def __init__(self, model_name: str = "microsoft/trocr-base-printed"):
        """
        Инициализация модели
        
        Args:
            model_name: Название модели из HuggingFace Hub
        """
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Используется устройство: {self.device}")
    
    def load_model(self) -> None:
        """Загрузка модели и процессора"""
        try:
            logger.info(f"Загрузка модели {self.model_name}")
            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("Модель успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {e}")
            raise
    
    def predict(self, image_data: str) -> Dict[str, Any]:
        """
        Распознавание формулы на изображении
        
        Args:
            image_data: Base64 encoded изображение
            
        Returns:
            Словарь с результатом распознавания
        """
        try:
            if not self.model or not self.processor:
                raise ValueError("Модель не загружена. Вызовите load_model() сначала")
            
            # Декодирование base64 изображения
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Подготовка изображения
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Генерация LaTeX кода
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values)
                generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            return {
                "success": True,
                "latex_code": generated_text,
                "confidence": 1.0,  # TrOCR не предоставляет confidence score
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Ошибка при распознавании: {e}")
            return {
                "success": False,
                "latex_code": None,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def validate_image(self, image_data: str) -> Dict[str, Any]:
        """
        Валидация входного изображения
        
        Args:
            image_data: Base64 encoded изображение
            
        Returns:
            Результат валидации
        """
        try:
            # Проверка base64
            image_bytes = base64.b64decode(image_data)
            
            # Проверка что это валидное изображение
            image = Image.open(io.BytesIO(image_bytes))
            
            # Проверка размеров
            width, height = image.size
            if width < 32 or height < 32:
                return {
                    "valid": False,
                    "error": f"Изображение слишком маленькое: {width}x{height}. Минимум 32x32"
                }
            
            if width > 2048 or height > 2048:
                return {
                    "valid": False,
                    "error": f"Изображение слишком большое: {width}x{height}. Максимум 2048x2048"
                }
            
            return {
                "valid": True,
                "width": width,
                "height": height,
                "format": image.format,
                "error": None
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Ошибка валидации изображения: {str(e)}"
            }


# Глобальный экземпляр модели
_model_instance: Optional[Formula2LaTeXModel] = None


def get_model() -> Formula2LaTeXModel:
    """Получение экземпляра модели (singleton pattern)"""
    global _model_instance
    if _model_instance is None:
        _model_instance = Formula2LaTeXModel()
        _model_instance.load_model()
    return _model_instance