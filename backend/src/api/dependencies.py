
from domain.interfaces.repositories import (
    UserRepositoryInterface,
    WalletRepositoryInterface,
    TaskRepositoryInterface,
    MLModelRepositoryInterface
)
from domain.interfaces.services import (
    UserServiceInterface,
    PasswordServiceInterface,
    MessagingServiceInterface
)
from domain.services.user_service import UserAuthService
from domain.services.task_service import TaskManagementService
from domain.services.wallet_service import WalletManagementService

from infrastructure.container import get_container


def get_user_repository() -> UserRepositoryInterface:
    container = get_container()
    return container.get(UserRepositoryInterface)


def get_wallet_repository() -> WalletRepositoryInterface:
    container = get_container()
    return container.get(WalletRepositoryInterface)


def get_task_repository() -> TaskRepositoryInterface:
    container = get_container()
    return container.get(TaskRepositoryInterface)


def get_ml_model_repository() -> MLModelRepositoryInterface:
    container = get_container()
    return container.get(MLModelRepositoryInterface)


def get_password_service() -> PasswordServiceInterface:
    container = get_container()
    return container.get(PasswordServiceInterface)


def get_messaging_service() -> MessagingServiceInterface:
    container = get_container()
    return container.get(MessagingServiceInterface)


def get_user_service() -> UserServiceInterface:
    container = get_container()
    return container.get(UserServiceInterface)


# Глобальный экземпляр сервиса для сохранения состояния
_task_service_instance = None

def get_task_service():
    global _task_service_instance
    
    if _task_service_instance is None:
        # Создаем упрощенный сервис для демонстрации
        class SimpleTaskService:
            def __init__(self):
                from infrastructure.database import SessionLocal
                self.db = SessionLocal()
                self._tasks = {}
                self._start_result_processor()
                
            def create_prediction_task(self, user, model_id, file_content, filename):
                from uuid import uuid4
                from datetime import datetime
                import json
                import pika
                import os
                from infrastructure.models import Task, TaskStatus, File, MLModel
                from sqlalchemy.orm import sessionmaker
                from infrastructure.database import engine
                
                Session = sessionmaker(bind=engine)
                db = Session()
                
                try:
                    task_id = uuid4()
                    
                    file_obj = File(
                        path=f"temp/{filename}",
                        content_type="image/png",
                        original_filename=filename,
                        size=len(file_content)
                    )
                    db.add(file_obj)
                    db.flush()
                    
                    print(f"DEBUG: Creating task with model_id: {model_id}")
                    
                    task_obj = Task(
                        id=task_id,
                        user_id=user.id,
                        file_id=file_obj.id,
                        model_id=model_id,
                        status=TaskStatus.PENDING,
                        credits_charged=2.50,
                        input_data=file_content[:100] + "..." if len(file_content) > 100 else file_content
                    )
                    db.add(task_obj)
                    db.commit()
                    
                    task = {
                        "id": str(task_id),
                        "status": "pending", 
                        "credits_charged": "2.50",
                        "created_at": task_obj.created_at.isoformat(),
                        "user_id": str(user.id),
                        "output": None,
                        "error": None,
                        "_timestamp": task_obj.created_at.isoformat()
                    }
                    
                    self._tasks[str(task_id)] = task
                    
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()
                
                try:
                    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
                    credentials = pika.PlainCredentials('guest', 'guest')
                    parameters = pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
                    connection = pika.BlockingConnection(parameters)
                    channel = connection.channel()
                    
                    channel.exchange_declare(exchange='formula_tasks', exchange_type='direct', durable=True)
                    channel.queue_declare(
                        queue='formula_recognition_queue', 
                        durable=True,
                        arguments={
                            'x-dead-letter-exchange': '',
                            'x-dead-letter-routing-key': 'formula_dead_letter_queue',
                            'x-message-ttl': 3600000
                        }
                    )
                    channel.queue_bind(exchange='formula_tasks', queue='formula_recognition_queue', routing_key='formula.recognition')
                    
                    ml_task_data = {
                        "task_id": str(task_id),
                        "user_id": str(user.id),
                        "model_id": str(model_id),
                        "image_data": file_content,
                        "filename": filename,
                        "timestamp": datetime.now().timestamp()
                    }
                    print(f"DEBUG: Sending to RabbitMQ with model_id: {model_id}")
                    
                    channel.basic_publish(
                        exchange='formula_tasks',
                        routing_key='formula.recognition',
                        body=json.dumps(ml_task_data, ensure_ascii=False),
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            content_type='application/json',
                            message_id=str(task_id)
                        )
                    )
                    
                    connection.close()
                    self._tasks[str(task_id)]["status"] = "in_progress"
                    
                except Exception as e:
                    self._tasks[str(task_id)]["status"] = "error"
                    self._tasks[str(task_id)]["error"] = f"Failed to queue task: {str(e)}"
                
                return task
                
            def get_user_tasks(self, user):
                from types import SimpleNamespace
                from infrastructure.models import Task
                from sqlalchemy.orm import sessionmaker
                from infrastructure.database import engine
                
                Session = sessionmaker(bind=engine)
                db = Session()
                
                try:
                    db_tasks = db.query(Task).filter(Task.user_id == user.id).order_by(Task.created_at.desc()).all()
                    
                    result = []
                    for task in db_tasks:
                        task_obj = SimpleNamespace()
                        task_obj.id = str(task.id)
                        task_obj.status = task.status.value
                        task_obj.credits_charged = str(task.credits_charged)
                        task_obj.output = task.output_data
                        task_obj.error = task.error_message
                        task_obj._timestamp = task.created_at.isoformat()
                        result.append(task_obj)
                        
                    return result
                    
                finally:
                    db.close()
                
            def get_task_by_id(self, user, task_id):
                from types import SimpleNamespace
                from infrastructure.models import Task
                from sqlalchemy.orm import sessionmaker
                from infrastructure.database import engine
                from uuid import UUID
                
                Session = sessionmaker(bind=engine)
                db = Session()
                
                try:
                    try:
                        task_uuid = UUID(str(task_id))
                    except ValueError:
                        raise ValueError("Task not found")
                        
                    task = db.query(Task).filter(Task.id == task_uuid, Task.user_id == user.id).first()
                    
                    if not task:
                        raise ValueError("Task not found")
                    
                    task_obj = SimpleNamespace()
                    task_obj.id = str(task.id)
                    task_obj.status = task.status.value
                    task_obj.credits_charged = str(task.credits_charged)
                    task_obj.output = task.output_data
                    task_obj.error = task.error_message
                    task_obj._timestamp = task.created_at.isoformat()
                    
                    return task_obj
                    
                finally:
                    db.close()
                
            def get_task_result_sync(self, task_id, timeout):
                import pika
                import json
                import os
                from datetime import datetime
                
                task_id_str = str(task_id)
                
                if task_id_str in self._tasks:
                    task = self._tasks[task_id_str]
                    if task["status"] == "done":
                        return {
                            "task_id": task_id_str,
                            "status": "done",
                            "result": task["output"]
                        }
                    elif task["status"] == "error":
                        return {
                            "task_id": task_id_str,
                            "status": "error",
                            "error": task["error"]
                        }
                
                try:
                    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
                    credentials = pika.PlainCredentials('guest', 'guest')
                    parameters = pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
                    connection = pika.BlockingConnection(parameters)
                    channel = connection.channel()
                    
                    channel.exchange_declare(exchange='formula_results', exchange_type='direct', durable=True)
                    channel.queue_declare(queue='formula_results_queue', durable=True)
                    
                    method_frame, header_frame, body = channel.basic_get(queue='formula_results_queue')
                    
                    if method_frame:
                        try:
                            data = json.loads(body.decode('utf-8'))
                            if data.get('task_id') == task_id_str:
                                if task_id_str in self._tasks:
                                    if data.get('success', False):
                                        self._tasks[task_id_str]["status"] = "done"
                                        self._tasks[task_id_str]["output"] = data.get('latex_code', '')
                                        result = {
                                            "task_id": task_id_str,
                                            "status": "done",
                                            "result": data.get('latex_code', '')
                                        }
                                    else:
                                        self._tasks[task_id_str]["status"] = "error"
                                        self._tasks[task_id_str]["error"] = data.get('error', 'Unknown error')
                                        result = {
                                            "task_id": task_id_str,
                                            "status": "error",
                                            "error": data.get('error', 'Unknown error')
                                        }
                                    
                                    channel.basic_ack(method_frame.delivery_tag)
                                    connection.close()
                                    return result
                            
                            channel.basic_ack(method_frame.delivery_tag)
                        except:
                            channel.basic_ack(method_frame.delivery_tag)
                    
                    connection.close()
                    return None
                    
                except Exception as e:
                    return None
                    
            def _start_result_processor(self):
                import threading
                import time
                
                def process_results():
                    import pika
                    import json
                    import os
                    
                    while True:
                        try:
                            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
                            credentials = pika.PlainCredentials('guest', 'guest')
                            parameters = pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
                            connection = pika.BlockingConnection(parameters)
                            channel = connection.channel()
                            
                            channel.exchange_declare(exchange='formula_results', exchange_type='direct', durable=True)
                            channel.queue_declare(queue='formula_results_queue', durable=True)
                            
                            method_frame, header_frame, body = channel.basic_get(queue='formula_results_queue')
                            
                            if method_frame:
                                try:
                                    data = json.loads(body.decode('utf-8'))
                                    task_id = data.get('task_id')
                                    
                                    from infrastructure.models import Task, TaskStatus
                                    from sqlalchemy.orm import sessionmaker
                                    from infrastructure.database import engine
                                    from uuid import UUID
                                    
                                    Session = sessionmaker(bind=engine)
                                    db = Session()
                                    
                                    try:
                                        task_uuid = UUID(task_id)
                                        task = db.query(Task).filter(Task.id == task_uuid).first()
                                        
                                        if task:
                                            if data.get('success', False):
                                                task.status = TaskStatus.DONE
                                                task.output_data = data.get('latex_code', '')
                                                task.error_message = None
                                            else:
                                                task.status = TaskStatus.ERROR
                                                task.error_message = data.get('error', 'Unknown error')
                                                task.output_data = None
                                            
                                            db.commit()
                                            
                                            if task_id in self._tasks:
                                                self._tasks[task_id]["status"] = task.status.value
                                                self._tasks[task_id]["output"] = task.output_data
                                                self._tasks[task_id]["error"] = task.error_message
                                                
                                    except Exception as e:
                                        db.rollback()
                                        print(f"DEBUG: Error updating task in DB: {e}")
                                    finally:
                                        db.close()
                                    
                                    channel.basic_ack(method_frame.delivery_tag)
                                except Exception as e:
                                    print(f"DEBUG: Error processing result: {e}")
                                    channel.basic_ack(method_frame.delivery_tag)
                            
                            connection.close()
                            time.sleep(1)
                            
                        except Exception as e:
                            print(f"DEBUG: Result processor error: {e}")
                            time.sleep(5)
                
                thread = threading.Thread(target=process_results)
                thread.daemon = True
                thread.start()
        
        _task_service_instance = SimpleTaskService()
    
    return _task_service_instance


def get_wallet_service() -> WalletManagementService:
    # Простое создание сервиса без DI для тестирования
    from domain.services.wallet_service import WalletManagementService
    from infrastructure.database import SessionLocal
    from infrastructure.repositories import SQLAlchemyWalletRepository
    
    db = SessionLocal()
    return WalletManagementService(
        wallet_repo=SQLAlchemyWalletRepository(db)
    )