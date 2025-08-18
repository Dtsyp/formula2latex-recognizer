import logging
import base64
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form

from api.auth import get_current_user
from api.dependencies import get_task_service
from api.schemas import PredictionRequest, TaskResponse
from domain.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tasks"])

@router.post("/predict", response_model=TaskResponse)
async def create_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    task_service = Depends(get_task_service)
):
    """
    Создает задачу для распознавания формулы.
    Бизнес-логика вынесена в TaskService для лучшей масштабируемости.
    """
    # task_service уже получен через dependency injection
    
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

@router.post("/predict/upload", response_model=TaskResponse)
async def upload_and_predict(
    file: UploadFile = File(...),
    model_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    task_service = Depends(get_task_service)
):
    """
    Загружает файл и создает задачу для распознавания формулы.
    Принимает multipart/form-data с файлом и model_id.
    """
    try:
        # Читаем файл и конвертируем в base64
        file_contents = await file.read()
        file_content_base64 = base64.b64encode(file_contents).decode('utf-8')
        
        # Создаем PredictionRequest для использования существующей логики
        request = PredictionRequest(
            model_id=model_id,
            file_content=file_content_base64,
            filename=file.filename or "uploaded_file"
        )
        
        # Используем существующую логику создания задачи
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
        logger.error(f"Error creating upload prediction task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}"
        )

@router.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    current_user: User = Depends(get_current_user),
    task_service = Depends(get_task_service)
):
    """Получает все задачи пользователя"""
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
    task_service = Depends(get_task_service)
):
    """Получает конкретную задачу пользователя"""
    
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
    task_service = Depends(get_task_service),
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