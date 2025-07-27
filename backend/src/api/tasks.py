from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
import base64

from api.auth import get_current_user, get_db
from api.schemas import PredictionRequest, TaskResponse
from infrastructure.repositories import MLModelRepository, WalletRepository, FileRepository
from domain.user import User
from domain.file import File as DomainFile

router = APIRouter(tags=["Tasks"])

@router.post("/predict", response_model=TaskResponse)
async def create_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Создание задачи распознавания формулы"""
    model_repo = MLModelRepository(db)
    wallet_repo = WalletRepository(db)
    file_repo = FileRepository(db)
    
    # Get model
    model = model_repo.get_by_id(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Check wallet balance
    wallet = wallet_repo.get_by_owner_id(current_user.id)
    if wallet.balance < model.credit_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits"
        )
    
    # Create file
    try:
        file_content = base64.b64decode(request.file_content)
        # Determine content type from filename
        content_type = "image/png"  # Default
        if request.filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = "image/jpeg"
        elif request.filename.lower().endswith('.gif'):
            content_type = "image/gif"
        
        domain_file = DomainFile(request.filename, content_type)
        
        # Execute task through domain logic
        task = current_user.execute_task(domain_file, model)
        
        # Update wallet balance in repository
        wallet_repo.add_transaction(wallet.transactions[-1])  # Last transaction from domain
        wallet_repo.update_balance(wallet.id, wallet.balance)
        
        return TaskResponse(
            id=task.id,
            status=task.status,
            credits_charged=task.credits_charged,
            output_data=task.output,
            error_message=task.error,
            created_at=task._timestamp
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )

@router.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(current_user: User = Depends(get_current_user)):
    """Получение истории задач пользователя"""
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
    """Получение информации о конкретной задаче"""
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