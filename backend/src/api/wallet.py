from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.auth import get_current_user, get_current_admin
from api.schemas import WalletResponse, TransactionResponse, TopUpRequest
from api.dependencies import get_wallet_service, get_user_service
from domain.user import User
from domain.services.wallet_service import WalletManagementService
from domain.services.user_service import UserAuthService

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletManagementService = Depends(get_wallet_service)
):
    """
    Получение информации о кошельке.
    
    Контроллер только преобразует HTTP запрос/ответ.
    Бизнес-логика делегирована в WalletManagementService.
    """
    wallet = wallet_service.get_user_wallet(current_user)
    return WalletResponse(id=wallet.id, balance=wallet.balance)


@router.post("/top-up", response_model=TransactionResponse)
async def top_up_wallet(
    request: TopUpRequest,
    current_user: User = Depends(get_current_admin),
    wallet_service: WalletManagementService = Depends(get_wallet_service)
):
    """
    Пополнение кошелька (только для администраторов).
    
    Бизнес-логика делегирована в WalletManagementService.
    """
    try:
        transaction = wallet_service.top_up_wallet(
            current_user, 
            request.amount, 
            "Пополнение администратором"
        )
        
        return TransactionResponse(
            id=transaction.id,
            type=transaction.transaction_type,
            amount=transaction.amount,
            post_balance=transaction.post_balance,
            created_at=transaction.timestamp
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/admin/top-up/{user_id}", response_model=TransactionResponse)
async def admin_top_up_user(
    user_id: str,
    request: TopUpRequest,
    current_user: User = Depends(get_current_admin),
    wallet_service: WalletManagementService = Depends(get_wallet_service),
    user_service: UserAuthService = Depends(get_user_service)
):
    """
    Администратор пополняет баланс другого пользователя.
    
    Бизнес-логика делегирована в сервисы.
    """
    try:
        from uuid import UUID
        target_user = user_service.get_user_by_id(UUID(user_id))
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        transaction = wallet_service.admin_top_up_user(
            current_user, 
            target_user, 
            request.amount
        )
        
        return TransactionResponse(
            id=transaction.id,
            type=transaction.transaction_type,
            amount=transaction.amount,
            post_balance=transaction.post_balance,
            created_at=transaction.timestamp
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletManagementService = Depends(get_wallet_service)
):
    """
    Получение истории транзакций.
    
    Бизнес-логика делегирована в WalletManagementService.
    """
    transactions = wallet_service.get_transaction_history(current_user)
    
    return [
        TransactionResponse(
            id=txn.id,
            type=txn.transaction_type,
            amount=txn.amount,
            post_balance=txn.post_balance,
            created_at=txn.timestamp
        )
        for txn in transactions
    ]


@router.get("/stats")
async def get_wallet_stats(
    current_user: User = Depends(get_current_user),
    wallet_service: WalletManagementService = Depends(get_wallet_service)
):
    """
    Получение статистики по кошельку.
    
    Эндпоинт для демонстрации возможностей доменного сервиса.
    """
    stats = wallet_service.get_wallet_stats(current_user)
    return stats