from fastapi import APIRouter, Depends, HTTPException
from typing import List

from api.auth import get_current_user, get_current_admin, get_db
from api.schemas import WalletResponse, TransactionResponse, TopUpRequest
from infrastructure.repositories import WalletRepository
from domain.user import User

router = APIRouter(prefix="/wallet", tags=["Wallet"])

@router.get("", response_model=WalletResponse)
async def get_wallet(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Получение информации о кошельке"""
    wallet_repo = WalletRepository(db)
    wallet = wallet_repo.get_by_owner_id(current_user.id)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletResponse(id=wallet.id, balance=wallet.balance)

@router.post("/top-up", response_model=TransactionResponse)
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

@router.get("/transactions", response_model=List[TransactionResponse])
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