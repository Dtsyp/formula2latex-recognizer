from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from api.auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from api.schemas import UserRegister, UserLogin, Token, UserResponse
from api.dependencies import get_user_service
from domain.user import User
from domain.services.user_service import UserAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister, 
    user_service: UserAuthService = Depends(get_user_service)
):
    """
    Регистрация нового пользователя.
    
    Контроллер только преобразует HTTP запрос/ответ.
    Вся бизнес-логика делегирована в UserAuthService.
    """
    try:
        user = user_service.register_user(user_data.email, user_data.password)
        return UserResponse(id=user.id, email=user.email, role=user.role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin, 
    user_service: UserAuthService = Depends(get_user_service)
):
    """
    Авторизация пользователя.
    
    Контроллер только преобразует HTTP запрос/ответ.
    Вся логика аутентификации делегирована в UserAuthService.
    """
    user = user_service.authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем JWT токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе.
    """
    return UserResponse(
        id=current_user.id, 
        email=current_user.email, 
        role=current_user.role,
        is_active=current_user.is_active
    )


@router.put("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    user_service: UserAuthService = Depends(get_user_service)
):
    """
    Смена пароля пользователя.
    
    Бизнес-логика делегирована в UserAuthService.
    """
    try:
        success = user_service.change_password(current_user, old_password, new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный старый пароль"
            )
        
        return {"message": "Пароль успешно изменен"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/change-email", response_model=UserResponse)
async def change_email(
    new_email: str,
    current_user: User = Depends(get_current_user),
    user_service: UserAuthService = Depends(get_user_service)
):
    """
    Смена email пользователя.
    
    Бизнес-логика делегирована в UserAuthService.
    """
    try:
        updated_user = user_service.change_email(current_user, new_email)
        return UserResponse(
            id=updated_user.id, 
            email=updated_user.email, 
            role=updated_user.role,
            is_active=updated_user.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )