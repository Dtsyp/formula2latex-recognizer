import base64
import io
from typing import Dict, Any
from PIL import Image

from domain.interfaces.ml_model import ImageValidatorInterface


class ImageValidationService(ImageValidatorInterface):
    """
    Конкретная реализация валидатора изображений.
    
    Реализует интерфейс из доменного слоя - правильное направление зависимостей.
    """
    
    def validate_format(self, image_data: str) -> Dict[str, Any]:
        """Валидировать формат изображения"""
        try:
            # Декодируем base64
            image_bytes = base64.b64decode(image_data)
            
            # Проверяем что это изображение
            image = Image.open(io.BytesIO(image_bytes))
            
            # Проверяем поддерживаемые форматы
            supported_formats = ['PNG', 'JPEG', 'JPG', 'GIF']
            if image.format not in supported_formats:
                return {
                    'valid': False,
                    'error': f"Неподдерживаемый формат: {image.format}. Поддерживаются: {supported_formats}"
                }
            
            return {
                'valid': True,
                'format': image.format,
                'error': None
            }
            
        except base64.binascii.Error:
            return {
                'valid': False,
                'error': "Невалидные данные base64"
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f"Ошибка обработки изображения: {str(e)}"
            }
    
    def validate_size(self, image_data: str, max_width: int = 2048, max_height: int = 2048) -> Dict[str, Any]:
        """Валидировать размер изображения"""
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            width, height = image.size
            
            if width > max_width or height > max_height:
                return {
                    'valid': False,
                    'error': f"Изображение слишком большое: {width}x{height}. Максимум: {max_width}x{max_height}",
                    'current_size': {'width': width, 'height': height},
                    'max_size': {'width': max_width, 'height': max_height}
                }
            
            # Проверяем минимальный размер
            min_width, min_height = 50, 50
            if width < min_width or height < min_height:
                return {
                    'valid': False,
                    'error': f"Изображение слишком маленькое: {width}x{height}. Минимум: {min_width}x{min_height}",
                    'current_size': {'width': width, 'height': height},
                    'min_size': {'width': min_width, 'height': min_height}
                }
            
            return {
                'valid': True,
                'width': width,
                'height': height,
                'error': None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Ошибка проверки размера: {str(e)}"
            }
    
    def validate_content(self, image_data: str) -> Dict[str, Any]:
        """
        Валидировать содержимое изображения.
        
        Простая проверка - в продакшене можно добавить ML модель
        для проверки наличия формул/математических выражений.
        """
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Простая проверка - изображение не должно быть полностью черным или белым
            extrema = image.getextrema()
            
            # Проверяем все ли пиксели одинаковые (может быть пустое изображение)
            all_same = all(
                channel_min == channel_max 
                for channel_min, channel_max in extrema
            )
            
            if all_same:
                return {
                    'valid': False,
                    'error': "Изображение кажется пустым или однотонным"
                }
            
            return {
                'valid': True,
                'has_content': True,
                'error': None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Ошибка анализа содержимого: {str(e)}"
            }
    
    def get_image_info(self, image_data: str) -> Dict[str, Any]:
        """Получить полную информацию об изображении"""
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            return {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.size[0],
                'height': image.size[1],
                'file_size_bytes': len(image_bytes),
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
        except Exception as e:
            return {
                'error': f"Ошибка получения информации: {str(e)}"
            }