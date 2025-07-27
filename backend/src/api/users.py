from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from api.auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_user, get_db, ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.schemas import UserRegister, UserLogin, Token, UserResponse
from infrastructure.repositories import UserRepository
from domain.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
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

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db = Depends(get_db)):
    """Авторизация пользователя"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(user_data.email)
    
    if not user or not user_repo.verify_password(user_data.password, user.password_hash):
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

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return UserResponse(id=current_user.id, email=current_user.email)