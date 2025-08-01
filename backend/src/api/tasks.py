import base64
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import get_current_user, get_db
from api.schemas import PredictionRequest, TaskResponse
from domain.file import File as DomainFile
from domain.user import User
from infrastructure.messaging import get_messaging
from infrastructure.models import File
from infrastructure.repositories import MLModelRepository, WalletRepository, TaskRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tasks"])

@router.post("/predict", response_model=TaskResponse)
async def create_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    model_repo = MLModelRepository(db)
    wallet_repo = WalletRepository(db)
    task_repo = TaskRepository(db)
    messaging = get_messaging()
    
    model = model_repo.get_by_id(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    wallet = wallet_repo.get_by_owner_id(current_user.id)
    if wallet.balance < model.credit_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits"
        )
    
    try:
        try:
            base64.b64decode(request.file_content)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 image data"
            )
        
        content_type = "image/png"
        if request.filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = "image/jpeg"
        elif request.filename.lower().endswith('.gif'):
            content_type = "image/gif"
        
        domain_file = DomainFile(request.filename, content_type)
        
        file_model = File(
            path=request.filename,
            content_type=content_type,
            original_filename=request.filename
        )
        db.add(file_model)
        db.commit()
        db.refresh(file_model)
        
        task = current_user.execute_task(domain_file, model)
        
        class FileWithId:
            def __init__(self, id, path, content_type):
                self.id = id
                self.path = path
                self.content_type = content_type
        
        task._file = FileWithId(file_model.id, file_model.path, file_model.content_type)
        task_repo.create_task(task)
        
        task_data = {
            "task_id": str(task.id),
            "user_id": str(current_user.id),
            "image_data": request.file_content,
            "filename": request.filename,
            "model_id": str(request.model_id)
        }
        
        ml_task_id = messaging.publish_task(task_data)
        logger.info(f"Task {task.id} published to RabbitMQ as {ml_task_id}")
        
        if wallet.transactions:
            wallet_repo.add_transaction(wallet.transactions[-1])
        wallet_repo.update_balance(wallet.id, wallet.balance)
        
        return TaskResponse(
            id=task.id,
            status="pending",
            credits_charged=task.credits_charged,
            output_data=None,
            error_message=None,
            created_at=task._timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating prediction task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process task: {str(e)}"
        )

@router.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(current_user: User = Depends(get_current_user)):
    tasks = current_user.get_tasks()
    
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
    current_user: User = Depends(get_current_user)
):
    user_tasks = current_user.get_tasks()
    task = next((t for t in user_tasks if t.id == task_id), None)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        id=task.id,
        status=task.status,
        credits_charged=task.credits_charged,
        output_data=task.output,
        error_message=task.error,
        created_at=task._timestamp
    )