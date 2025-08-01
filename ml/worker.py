import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from messaging import get_rabbitmq_manager, RabbitMQManager
from model import get_model, Formula2LaTeXModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FormulaWorker:
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.rabbitmq_manager: RabbitMQManager = None
        self.ml_model: Formula2LaTeXModel = None
        self.running = True
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Получен сигнал {signum}. Завершение работы воркера {self.worker_id}")
        self.running = False
        if self.rabbitmq_manager:
            self.rabbitmq_manager.channel.stop_consuming()
    
    def initialize(self) -> None:
        try:
            logger.info(f"Инициализация воркера {self.worker_id}")
            
            self.rabbitmq_manager = get_rabbitmq_manager()
            logger.info("RabbitMQ подключен")
            
            self.ml_model = get_model()
            logger.info("ML модель загружена")
            
            logger.info(f"Воркер {self.worker_id} успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации воркера {self.worker_id}: {e}")
            raise
    
    def validate_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            required_fields = ['task_id', 'user_id', 'image_data']
            for field in required_fields:
                if field not in task_data:
                    return {
                        "valid": False,
                        "error": f"Отсутствует обязательное поле: {field}"
                    }
            
            image_validation = self.ml_model.validate_image(task_data['image_data'])
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
    
    def process_task(self, delivery_tag: str, task_data: Dict[str, Any]) -> None:
        task_id = task_data.get('task_id', 'unknown')
        start_time = time.time()
        
        try:
            logger.info(f"Обработка задачи {task_id} воркером {self.worker_id}")
            
            validation_result = self.validate_task_data(task_data)
            if not validation_result['valid']:
                self._send_error_result(task_data, validation_result['error'])
                self.rabbitmq_manager.ack_message(delivery_tag)
                return
            
            prediction_result = self.ml_model.predict(task_data['image_data'])
            processing_time = time.time() - start_time
            
            result_data = {
                "task_id": task_id,
                "user_id": task_data['user_id'],
                "worker_id": self.worker_id,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": processing_time,
                "success": prediction_result['success'],
                "latex_code": prediction_result['latex_code'],
                "confidence": prediction_result['confidence'],
                "error": prediction_result['error'],
                "image_info": validation_result.get('image_info', {})
            }
            
            self.rabbitmq_manager.publish_result(result_data)
            self.rabbitmq_manager.ack_message(delivery_tag)
            
            status = "успешно" if prediction_result['success'] else "с ошибкой"
            logger.info(f"Задача {task_id} обработана {status} за {processing_time:.2f}с")
            
        except Exception as e:
            logger.error(f"Ошибка обработки задачи {task_id}: {e}")
            self._send_error_result(task_data, str(e))
            self.rabbitmq_manager.nack_message(delivery_tag, requeue=False)
    
    def _send_error_result(self, task_data: Dict[str, Any], error_message: str) -> None:
        try:
            result_data = {
                "task_id": task_data.get('task_id', 'unknown'),
                "user_id": task_data.get('user_id', 'unknown'),
                "worker_id": self.worker_id,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": 0.0,
                "success": False,
                "latex_code": None,
                "confidence": 0.0,
                "error": error_message,
                "image_info": {}
            }
            
            self.rabbitmq_manager.publish_result(result_data)
            
        except Exception as e:
            logger.error(f"Ошибка отправки результата с ошибкой: {e}")
    
    def start(self) -> None:
        try:
            logger.info(f"Запуск воркера {self.worker_id}")
            self.initialize()
            self.rabbitmq_manager.consume_tasks(self.process_task)
            
        except KeyboardInterrupt:
            logger.info(f"Воркер {self.worker_id} остановлен пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка воркера {self.worker_id}: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        try:
            logger.info(f"Очистка ресурсов воркера {self.worker_id}")
            if self.rabbitmq_manager:
                self.rabbitmq_manager.close()
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов: {e}")


def main():
    parser = argparse.ArgumentParser(description='ML воркер для распознавания формул')
    parser.add_argument('--worker-id', required=True, help='ID воркера')
    
    args = parser.parse_args()
    
    worker = FormulaWorker(args.worker_id)
    worker.start()


if __name__ == "__main__":
    main()