"""
Модуль для работы с RabbitMQ в backend
Публикация задач и получение результатов
"""

import json
import logging
import os
import asyncio
from typing import Dict, Any, Optional, Callable
import pika
from datetime import datetime
import uuid

from domain.interfaces.services import MessagingServiceInterface

logger = logging.getLogger(__name__)


class BackendMessaging:
    """Класс для работы с RabbitMQ из backend"""
    
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.username = os.getenv('RABBITMQ_USERNAME', 'guest')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'guest')
        self.virtual_host = os.getenv('RABBITMQ_VHOST', '/')
        
        # Настройки очередей
        self.task_exchange = 'formula_tasks'
        self.result_exchange = 'formula_results'  
        self.result_queue = 'formula_results_queue'
        
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        
        # Хранилище результатов (в production использовать Redis)
        self._results_store: Dict[str, Dict[str, Any]] = {}
    
    def connect(self) -> None:
        """Подключение к RabbitMQ"""
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
            
            # Объявляем exchanges и очереди
            self._setup_exchanges_and_queues()
            
            logger.info(f"Backend подключен к RabbitMQ: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Ошибка подключения backend к RabbitMQ: {e}")
            raise
    
    def _setup_exchanges_and_queues(self) -> None:
        """Настройка exchanges и очередей"""
        if not self.channel:
            raise ValueError("Нет подключения к RabbitMQ")
        
        # Exchange для результатов
        self.channel.exchange_declare(
            exchange=self.result_exchange,
            exchange_type='direct',
            durable=True
        )
        
        # Очередь результатов
        self.channel.queue_declare(
            queue=self.result_queue,
            durable=True
        )
        
        # Привязка очереди результатов
        self.channel.queue_bind(
            exchange=self.result_exchange,
            queue=self.result_queue,
            routing_key='formula.result'
        )
    
    def publish_task(self, task_data: Dict[str, Any]) -> str:
        """
        Публикация задачи для обработки ML воркерами
        
        Args:
            task_data: Данные задачи
            
        Returns:
            ID задачи
        """
        if not self.channel:
            self.connect()
        
        try:
            task_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().timestamp()
            
            # Подготовка данных задачи
            message_data = {
                "task_id": task_id,
                "user_id": task_data["user_id"],
                "image_data": task_data["image_data"], 
                "filename": task_data.get("filename", "unknown.png"),
                "model_id": task_data.get("model_id"),
                "timestamp": timestamp
            }
            
            message = json.dumps(message_data, ensure_ascii=False)
            
            # Публикация задачи
            self.channel.basic_publish(
                exchange=self.task_exchange,
                routing_key='formula.recognition',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json',
                    message_id=task_id,
                    timestamp=int(timestamp)
                )
            )
            
            logger.info(f"Задача {task_id} опубликована в очереди")
            return task_id
            
        except Exception as e:
            logger.error(f"Ошибка публикации задачи: {e}")
            raise
    
    def get_task_result(self, task_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Получение результата задачи (синхронное ожидание)
        
        Args:
            task_id: ID задачи
            timeout: Таймаут ожидания в секундах
            
        Returns:
            Результат задачи или None если таймаут
        """
        # Проверяем кэш результатов
        if task_id in self._results_store:
            return self._results_store[task_id]
        
        if not self.channel:
            self.connect()
        
        try:
            # Подписываемся на результаты
            self._start_result_consumer()
            
            # Ожидаем результат
            start_time = datetime.utcnow().timestamp()
            while (datetime.utcnow().timestamp() - start_time) < timeout:
                # Обрабатываем сообщения неблокирующим способом
                method_frame, header_frame, body = self.channel.basic_get(
                    queue=self.result_queue, 
                    auto_ack=True
                )
                
                if method_frame:
                    self._process_result_message(body)
                    
                    # Проверяем появился ли наш результат
                    if task_id in self._results_store:
                        return self._results_store[task_id]
                
                # Небольшая пауза
                asyncio.sleep(0.1)
            
            logger.warning(f"Таймаут ожидания результата для задачи {task_id}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения результата задачи {task_id}: {e}")
            return None
    
    def _start_result_consumer(self) -> None:
        """Запуск потребителя результатов"""
        if not self.channel:
            raise ValueError("Нет подключения к RabbitMQ")
    
    def _process_result_message(self, body: bytes) -> None:
        """Обработка сообщения с результатом"""
        try:
            result_data = json.loads(body.decode('utf-8'))
            task_id = result_data.get('task_id')
            
            if task_id:
                self._results_store[task_id] = result_data
                logger.info(f"Получен результат для задачи {task_id}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки результата: {e}")
    
    def close(self) -> None:
        """Закрытие соединения"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.error(f"Ошибка закрытия соединения: {e}")


# Глобальный экземпляр
_messaging_instance: Optional[BackendMessaging] = None


class RabbitMQMessagingService(MessagingServiceInterface):
    
    def __init__(self):
        self._backend_messaging = BackendMessaging()
    
    def send_task(self, task_data: Dict[str, Any]) -> bool:
        try:
            task_id = self._backend_messaging.publish_task(task_data)
            return task_id is not None
        except Exception as e:
            logger.error(f"Ошибка отправки задачи: {e}")
            return False
    
    def receive_result(self, task_id: str) -> Dict[str, Any]:
        try:
            result = self._backend_messaging.get_task_result(task_id)
            return result if result is not None else {"task_id": task_id, "status": "pending"}
        except Exception as e:
            logger.error(f"Ошибка получения результата: {e}")
            return {"error": str(e)}
    
    def publish_notification(self, user_id: str, message: str) -> bool:
        try:
            logger.info(f"Отправка уведомления пользователю {user_id}: {message}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            return False


def get_messaging() -> BackendMessaging:
    global _messaging_instance
    if _messaging_instance is None:
        _messaging_instance = BackendMessaging()
    return _messaging_instance