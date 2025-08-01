import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from api.auth import get_current_user, get_db
from api.schemas import PredictionRequest, TaskResponse
from domain.user import User
from infrastructure.messaging import get_messaging
from services.task_service import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tasks"])

@router.post("/predict", response_model=TaskResponse)
async def create_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Создает задачу для распознавания формулы.
    Бизнес-логика вынесена в TaskService для лучшей масштабируемости.
    """
    messaging = get_messaging()
    task_service = TaskService(db, messaging)
    
    try:
        result = task_service.create_prediction_task(
            user=current_user,
            model_id=request.model_id,
            file_content=request.file_content,
            filename=request.filename
        )
        
        return TaskResponse(
            id=result["id"],
            status=result["status"],
            credits_charged=result["credits_charged"],
            output_data=None,
            error_message=None,
            created_at=result["created_at"]
        )
        
    except ValueError as e:
        if "Model not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Insufficient credits" in str(e):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error creating prediction task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process task: {str(e)}"
        )

@router.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получает все задачи пользователя"""
    messaging = get_messaging()
    task_service = TaskService(db, messaging)
    tasks = task_service.get_user_tasks(current_user)
    
    return [
        TaskResponse(
            id=task.id,
            status=task.status,
            credits_charged=task.credits_charged,
            output_data=task.output,
            error_message=task.error,
            created_at=task._timestamp
        )
        for task in tasks
    ]

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Получает конкретную задачу пользователя"""
    messaging = get_messaging()
    task_service = TaskService(db, messaging)
    
    try:
        task = task_service.get_task_by_id(current_user, task_id)
        
        return TaskResponse(
            id=task.id,
            status=task.status,
            credits_charged=task.credits_charged,
            output_data=task.output,
            error_message=task.error,
            created_at=task._timestamp
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    timeout: int = Query(default=30, description="Timeout in seconds for waiting result")
):
    """
    Получает результат задачи напрямую из RabbitMQ очереди.
    
    Этот эндпоинт позволяет пользователю получить результат задачи немедленно
    из очереди результатов, не дожидаясь обновления в БД через Result Processor.
    
    Используется для:
    - Быстрого получения результатов через polling
    - WebSocket подключений для real-time уведомлений
    - Отладки и мониторинга системы
    """
    messaging = get_messaging()
    task_service = TaskService(db, messaging)
    
    # Проверяем что задача принадлежит пользователю
    try:
        task_service.get_task_by_id(current_user, task_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Получаем результат из очереди
    result = task_service.get_task_result_sync(task_id, timeout)
    
    if result is None:
        raise HTTPException(
            status_code=408, 
            detail=f"Result not ready within {timeout} seconds. Task may still be processing."
        )
    
    return result