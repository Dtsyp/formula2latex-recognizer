import json
import logging
import os
import signal
import sys
from typing import Dict, Any
from uuid import UUID

import pika
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_path)

from infrastructure.database import get_database_url
from infrastructure.models import TaskStatus
from infrastructure.repositories import TaskRepository, UserRepository

logger = logging.getLogger(__name__)


class ResultProcessor:
    
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.username = os.getenv('RABBITMQ_USERNAME', 'guest')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.virtual_host = os.getenv('RABBITMQ_VHOST', '/')
        
        self.result_queue = 'formula_results_queue'
        
        self.connection = None
        self.channel = None
        self.running = True
        
        # Настройка базы данных
        self.engine = create_engine(get_database_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Настройка обработки сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Получен сигнал {signum}. Завершение работы процессора результатов")
        self.running = False
        if self.channel:
            self.channel.stop_consuming()
    
    def connect(self) -> None:
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info("Процессор результатов подключен к RabbitMQ")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к RabbitMQ: {e}")
            raise
    
    def process_result(self, ch, method, properties, body) -> None:
        """
        Обработка результата от ML воркера
        
        Args:
            ch: Канал RabbitMQ
            method: Метод доставки
            properties: Свойства сообщения  
            body: Тело сообщения
        """
        try:
            # Парсинг результата
            result_data = json.loads(body.decode('utf-8'))
            task_id = result_data.get('task_id')
            
            logger.info(f"Обработка результата для задачи {task_id}")
            
            # Получение сессии БД
            db = self.SessionLocal()
            
            try:
                # Поиск пользователя и обновление задачи
                user_repo = UserRepository(db)
                task_repo = TaskRepository(db)
                
                user_id = result_data.get('user_id')
                user = user_repo.get_by_id(user_id)
                
                if not user:
                    logger.error(f"Пользователь {user_id} не найден для задачи {task_id}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                try:
                    task_uuid = UUID(task_id)
                    task = task_repo.get_by_id(task_uuid)
                except ValueError:
                    logger.error(f"Невалидный UUID задачи: {task_id}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                if not task:
                    logger.error(f"Задача {task_id} не найдена для пользователя {user_id}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                if result_data.get('success', False):
                    task.status = TaskStatus.DONE
                    task.output_data = result_data.get('latex_code', '')
                    task.error_message = None
                    logger.info(f"Задача {task_id} выполнена успешно: {task.output_data}")
                else:
                    task.status = TaskStatus.ERROR
                    task.error_message = result_data.get('error', 'Unknown error')
                    task.output_data = None
                    logger.info(f"Задача {task_id} завершена с ошибкой: {task.error_message}")
                
                db.commit()
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Результат задачи {task_id} успешно обработан")
                
            except Exception as e:
                logger.error(f"Ошибка обработки результата задачи {task_id}: {e}")
                db.rollback()
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Критическая ошибка обработки результата: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self) -> None:
        try:
            if not self.channel:
                self.connect()
            
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.result_queue,
                on_message_callback=self.process_result
            )
            
            logger.info("Начало потребления результатов из очереди")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Остановка по запросу пользователя")
        except Exception as e:
            logger.error(f"Ошибка потребления результатов: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("Ресурсы процессора результатов очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки ресурсов: {e}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    processor = ResultProcessor()
    processor.start_consuming()


if __name__ == "__main__":
    main()