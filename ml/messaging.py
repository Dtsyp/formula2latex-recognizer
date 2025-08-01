"""
Модуль для работы с RabbitMQ
Настройка очередей и exchange для ML задач
"""

import json
import logging
import os
from typing import Dict, Any, Callable, Optional
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic

logger = logging.getLogger(__name__)


class RabbitMQConfig:
    """Конфигурация RabbitMQ"""
    
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.username = os.getenv('RABBITMQ_USERNAME', 'guest')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.virtual_host = os.getenv('RABBITMQ_VHOST', '/')
        
        # Настройки очередей
        self.task_exchange = 'formula_tasks'
        self.task_queue = 'formula_recognition_queue'
        self.result_exchange = 'formula_results'
        self.result_queue = 'formula_results_queue'
        self.dead_letter_queue = 'formula_dead_letter_queue'


class RabbitMQManager:
    """Менеджер для работы с RabbitMQ"""
    
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
    
    def connect(self) -> None:
        """Подключение к RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                self.config.username, 
                self.config.password
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config.host,
                port=self.config.port,
                virtual_host=self.config.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info(f"Подключение к RabbitMQ установлено: {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к RabbitMQ: {e}")
            raise
    
    def setup_queues(self) -> None:
        """Настройка exchanges и очередей"""
        if not self.channel:
            raise ValueError("Нет подключения к RabbitMQ")
        
        try:
            # Exchange для задач
            self.channel.exchange_declare(
                exchange=self.config.task_exchange,
                exchange_type='direct',
                durable=True
            )
            
            # Exchange для результатов
            self.channel.exchange_declare(
                exchange=self.config.result_exchange,
                exchange_type='direct',
                durable=True
            )
            
            # Dead Letter Queue
            self.channel.queue_declare(
                queue=self.config.dead_letter_queue,
                durable=True
            )
            
            # Основная очередь задач
            self.channel.queue_declare(
                queue=self.config.task_queue,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': self.config.dead_letter_queue,
                    'x-message-ttl': 3600000  # 1 час TTL
                }
            )
            
            # Очередь результатов
            self.channel.queue_declare(
                queue=self.config.result_queue,
                durable=True
            )
            
            # Привязка очередей к exchanges
            self.channel.queue_bind(
                exchange=self.config.task_exchange,
                queue=self.config.task_queue,
                routing_key='formula.recognition'
            )
            
            self.channel.queue_bind(
                exchange=self.config.result_exchange,
                queue=self.config.result_queue,
                routing_key='formula.result'
            )
            
            logger.info("Очереди RabbitMQ настроены успешно")
            
        except Exception as e:
            logger.error(f"Ошибка настройки очередей: {e}")
            raise
    
    def publish_task(self, task_data: Dict[str, Any]) -> None:
        """
        Публикация задачи в очередь
        
        Args:
            task_data: Данные задачи
        """
        if not self.channel:
            raise ValueError("Нет подключения к RabbitMQ")
        
        try:
            message = json.dumps(task_data, ensure_ascii=False)
            
            self.channel.basic_publish(
                exchange=self.config.task_exchange,
                routing_key='formula.recognition',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json',
                    message_id=task_data.get('task_id'),
                    timestamp=int(task_data.get('timestamp', 0))
                )
            )
            
            logger.info(f"Задача опубликована: {task_data.get('task_id')}")
            
        except Exception as e:
            logger.error(f"Ошибка публикации задачи: {e}")
            raise
    
    def publish_result(self, result_data: Dict[str, Any]) -> None:
        """
        Публикация результата
        
        Args:
            result_data: Данные результата
        """
        if not self.channel:
            raise ValueError("Нет подключения к RabbitMQ")
        
        try:
            message = json.dumps(result_data, ensure_ascii=False)
            
            self.channel.basic_publish(
                exchange=self.config.result_exchange,
                routing_key='formula.result',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                    message_id=result_data.get('task_id'),
                    correlation_id=result_data.get('task_id')
                )
            )
            
            logger.info(f"Результат опубликован: {result_data.get('task_id')}")
            
        except Exception as e:
            logger.error(f"Ошибка публикации результата: {e}")
            raise
    
    def consume_tasks(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Потребление задач из очереди
        
        Args:
            callback: Функция обратного вызова для обработки задач
        """
        if not self.channel:
            raise ValueError("Нет подключения к RabbitMQ")
        
        def wrapper(ch: BlockingChannel, method: Basic.Deliver, 
                   properties: pika.BasicProperties, body: bytes) -> None:
            try:
                task_data = json.loads(body.decode('utf-8'))
                
                # Вызов callback функции
                callback(method.delivery_tag, task_data)
                
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {e}")
                # Отклоняем сообщение и отправляем в DLQ
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        # Настройка QoS - обрабатывать по одному сообщению за раз
        self.channel.basic_qos(prefetch_count=1)
        
        # Подписка на очередь
        self.channel.basic_consume(
            queue=self.config.task_queue,
            on_message_callback=wrapper
        )
        
        logger.info("Начинаем потребление задач из очереди")
        self.channel.start_consuming()
    
    def ack_message(self, delivery_tag: str) -> None:
        """Подтверждение обработки сообщения"""
        if self.channel:
            self.channel.basic_ack(delivery_tag=delivery_tag)
    
    def nack_message(self, delivery_tag: str, requeue: bool = False) -> None:
        """Отклонение сообщения"""
        if self.channel:
            self.channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
    
    def close(self) -> None:
        """Закрытие соединения"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("Соединение с RabbitMQ закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения: {e}")


def get_rabbitmq_manager() -> RabbitMQManager:
    """Получение настроенного менеджера RabbitMQ"""
    config = RabbitMQConfig()
    manager = RabbitMQManager(config)
    manager.connect()
    manager.setup_queues()
    return manager