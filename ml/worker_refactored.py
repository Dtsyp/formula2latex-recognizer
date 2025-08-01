import argparse
import logging
import os
import signal
import sys
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from messaging import get_rabbitmq_manager
from model import get_model
from services.task_validator import TaskValidationService
from services.task_processor import TaskProcessingService
from services.result_publisher import ResultPublishingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerOrchestrator:
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.running = True
        
        # Dependencies будут инициализированы в initialize()
        self._rabbitmq_manager = None
        self._validator = None
        self._processor = None
        self._publisher = None
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Получен сигнал {signum}. Завершение работы воркера {self.worker_id}")
        self.running = False
        if self._rabbitmq_manager:
            self._rabbitmq_manager.channel.stop_consuming()
    
    def initialize(self) -> None:
        try:
            logger.info(f"Инициализация воркера {self.worker_id}")
            
            # Инициализация dependencies через DI
            self._rabbitmq_manager = get_rabbitmq_manager()
            ml_model = get_model()
            
            # Создание сервисов с инъекцией зависимостей
            self._validator = TaskValidationService(ml_model)
            self._processor = TaskProcessingService(ml_model)
            self._publisher = ResultPublishingService(self._rabbitmq_manager)
            
            logger.info(f"Воркер {self.worker_id} успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации воркера {self.worker_id}: {e}")
            raise
    
    def handle_task(self, ch, method, properties, body) -> None:
        delivery_tag = method.delivery_tag
        
        try:
            import json
            task_data = json.loads(body.decode('utf-8'))
            task_id = task_data.get('task_id', 'unknown')
            
            logger.info(f"Получена задача {task_id}")
            
            # 1. Валидация (делегирована в TaskValidationService)
            validation_result = self._validator.validate(task_data)
            if not validation_result['valid']:
                self._publisher.publish_error(task_data, validation_result['error'])
                self._rabbitmq_manager.ack_message(delivery_tag)
                return
            
            # 2. Обработка (делегирована в TaskProcessingService)
            result = self._processor.process(task_data)
            
            # 3. Публикация результата (делегирована в ResultPublishingService)
            self._publisher.publish_success(result)
            
            # 4. Подтверждение получения сообщения
            self._rabbitmq_manager.ack_message(delivery_tag)
            
        except Exception as e:
            logger.error(f"Критическая ошибка обработки задачи: {e}")
            try:
                task_data = json.loads(body.decode('utf-8'))
                self._publisher.publish_error(task_data, f"Критическая ошибка: {str(e)}")
            except:
                pass
            self._rabbitmq_manager.ack_message(delivery_tag)
    
    def start(self) -> None:
        if not all([self._rabbitmq_manager, self._validator, self._processor, self._publisher]):
            raise RuntimeError("Воркер не инициализирован. Вызовите initialize() сначала.")
        
        logger.info(f"Запуск воркера {self.worker_id}")
        
        try:
            self._rabbitmq_manager.channel.basic_consume(
                queue=self._rabbitmq_manager.config.task_queue,
                on_message_callback=self.handle_task
            )
            
            logger.info(f"Воркер {self.worker_id} ожидает задачи...")
            
            while self.running:
                try:
                    self._rabbitmq_manager.channel.start_consuming()
                except KeyboardInterrupt:
                    self.running = False
                    break
                    
        except Exception as e:
            logger.error(f"Ошибка в основном цикле воркера: {e}")
            raise
        finally:
            logger.info(f"Воркер {self.worker_id} остановлен")
            if self._rabbitmq_manager:
                try:
                    self._rabbitmq_manager.close()
                except:
                    pass


def main():
    parser = argparse.ArgumentParser(description='ML Worker для обработки задач распознавания формул')
    parser.add_argument('--worker-id', required=True, help='Уникальный ID воркера')
    args = parser.parse_args()
    
    worker = WorkerOrchestrator(args.worker_id)
    
    try:
        worker.initialize()
        worker.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения")
    except Exception as e:
        logger.error(f"Критическая ошибка воркера: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()