from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from typing import List
from uuid import UUID
import base64

from api.auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_user, get_current_admin, get_db, ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.schemas import (
    UserRegister, UserLogin, Token, UserResponse, WalletResponse,
    TransactionResponse, TopUpRequest, MLModelResponse, PredictionRequest,
    TaskResponse, ErrorResponse
)
from infrastructure.repositories import (
    UserRepository, WalletRepository, MLModelRepository, TaskRepository, FileRepository
)
from domain.user import User, Admin
from domain.file import File as DomainFile
from domain.task import RecognitionTask
from uuid import uuid4

app = FastAPI(
    title="Formula2LaTeX Recognizer API",
    description="REST API для распознавания математических формул с аутентификацией",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Formula2LaTeX Recognizer API", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "formula2latex-backend"}

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse, tags=["Authentication"])
async def register(user_data: UserRegister, db = Depends(get_db)):
    """Регистрация нового пользователя"""
    user_repo = UserRepository(db)
    
    # Check if user exists
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = user_repo.create_user(user_data.email, user_data.password)
    
    return UserResponse(id=user.id, email=user.email)

@app.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(user_data: UserLogin, db = Depends(get_db)):
    """Авторизация пользователя"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(user_data.email)
    
    if not user or not user_repo.verify_password(user_data.password, user._password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return UserResponse(id=current_user.id, email=current_user.email)

# Wallet endpoints
@app.get("/wallet", response_model=WalletResponse, tags=["Wallet"])
async def get_wallet(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Получение информации о кошельке"""
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_by_owner_id(current_user.id)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletResponse(id=wallet.id, balance=wallet.balance)

@app.post("/wallet/top-up", response_model=TransactionResponse, tags=["Wallet"])
async def top_up_wallet(
    request: TopUpRequest,
    current_user: User = Depends(get_current_admin),
    db = Depends(get_db)
):
    """Пополнение кошелька (только для администраторов)"""
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_by_owner_id(current_user.id)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    transaction = wallet.top_up(request.amount)
    wallet_repo.add_transaction(transaction)
    wallet_repo.update_balance(wallet.id, wallet.balance)
    
    return TransactionResponse(
        id=transaction.id,
        type="top_up",
        amount=transaction.amount,
        post_balance=transaction.post_balance,
        created_at=transaction.timestamp
    )

@app.get("/wallet/transactions", response_model=List[TransactionResponse], tags=["Wallet"])
async def get_transactions(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Получение истории транзакций"""
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_by_owner_id(current_user.id)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return [
        TransactionResponse(
            id=txn.id,
            type="top_up" if txn.amount > 0 else "spend",
            amount=abs(txn.amount),
            post_balance=txn.post_balance,
            created_at=txn.timestamp
        )
        for txn in wallet.transactions
    ]

# ML Models endpoints
@app.get("/models", response_model=List[MLModelResponse], tags=["ML Models"])
async def get_models(db = Depends(get_db)):
    """Получение списка доступных ML моделей"""
    model_repo = MLModelRepository(db)
    models = model_repo.get_active_models()
    
    return [
        MLModelResponse(
            id=model.id,
            name=model.name,
            credit_cost=model.credit_cost,
            is_active=True
        )
        for model in models
    ]

# Prediction endpoints
@app.post("/predict", response_model=TaskResponse, tags=["Predictions"])
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

@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
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

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
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