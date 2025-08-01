from typing import List
from uuid import UUID
from decimal import Decimal

from domain.user import User
from domain.wallet import Wallet, Transaction
from domain.interfaces.repositories import WalletRepositoryInterface
from domain.interfaces.services import WalletServiceInterface


class WalletManagementService(WalletServiceInterface):
    """
    Доменный сервис для управления кошельками пользователей.
    
    Инкапсулирует бизнес-логику работы с кошельками, которая ранее
    была разбросана по разным классам.
    
    Следует принципам:
    - Single Responsibility: только логика управления кошельками
    - Dependency Inversion: зависит от абстракций
    """
    
    def __init__(self, wallet_repo: WalletRepositoryInterface):
        self._wallet_repo = wallet_repo
    
    def get_user_wallet(self, user: User) -> Wallet:
        """
        Получить кошелек пользователя.
        
        Если кошелек не существует, создает новый.
        """
        wallet = self._wallet_repo.get_by_owner_id(user.id)
        
        if not wallet:
            # Создаем кошелек с нулевым балансом
            wallet = self._wallet_repo.create_wallet(user.id, Decimal("0"))
        
        return wallet
    
    def top_up_wallet(self, user: User, amount: Decimal, description: str = "Пополнение") -> Transaction:
        """
        Пополнить кошелек пользователя.
        
        Бизнес-правила:
        - Сумма должна быть положительной
        - Создается транзакция пополнения
        - Обновляется баланс кошелька
        """
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        
        wallet = self.get_user_wallet(user)
        
        # Создаем транзакцию пополнения
        transaction = wallet.top_up(amount)
        transaction.description = description
        
        # Сохраняем транзакцию
        saved_transaction = self._wallet_repo.add_transaction(transaction)
        
        # Обновляем баланс
        self._wallet_repo.update_balance(wallet.id, wallet.balance)
        
        return saved_transaction
    
    def charge_for_task(self, user: User, amount: Decimal, task_id: UUID) -> Transaction:
        """
        Списать средства за выполнение задачи.
        
        Бизнес-правила:
        - Должно быть достаточно средств на балансе
        - Создается транзакция списания
        - Обновляется баланс кошелька
        """
        if amount <= 0:
            raise ValueError("Сумма списания должна быть положительной")
        
        wallet = self.get_user_wallet(user)
        
        # Проверяем достаточность средств
        if wallet.balance < amount:
            raise ValueError(f"Недостаточно средств. Баланс: {wallet.balance}, требуется: {amount}")
        
        # Создаем транзакцию списания
        transaction = wallet.charge(amount)
        transaction.description = f"Списание за задачу {task_id}"
        transaction.task_id = task_id
        
        # Сохраняем транзакцию
        saved_transaction = self._wallet_repo.add_transaction(transaction)
        
        # Обновляем баланс
        self._wallet_repo.update_balance(wallet.id, wallet.balance)
        
        return saved_transaction
    
    def get_transaction_history(self, user: User, limit: int = 100) -> List[Transaction]:
        """Получить историю транзакций пользователя"""
        wallet = self.get_user_wallet(user)
        return self._wallet_repo.get_transactions(wallet.id, limit)
    
    def check_sufficient_funds(self, user: User, required_amount: Decimal) -> bool:
        """
        Проверить достаточность средств для операции.
        
        Args:
            user: Пользователь
            required_amount: Требуемая сумма
            
        Returns:
            True если средств достаточно, False иначе
        """
        if required_amount <= 0:
            return True
        
        wallet = self.get_user_wallet(user)
        return wallet.balance >= required_amount
    
    def get_balance(self, user: User) -> Decimal:
        """Получить текущий баланс пользователя"""
        wallet = self.get_user_wallet(user)
        return wallet.balance
    
    def admin_top_up_user(self, admin_user: User, target_user: User, amount: Decimal) -> Transaction:
        """
        Администратор пополняет баланс пользователя.
        
        Бизнес-правила:
        - Операцию может выполнить только администратор
        - Сумма должна быть положительной
        """
        if not admin_user.is_admin():
            raise ValueError("Только администратор может пополнять баланс других пользователей")
        
        return self.top_up_wallet(
            target_user, 
            amount, 
            f"Пополнение администратором {admin_user.email}"
        )
    
    def get_wallet_stats(self, user: User) -> dict:
        """
        Получить статистику по кошельку пользователя.
        
        Returns:
            dict с информацией о балансе, количестве транзакций и т.д.
        """
        wallet = self.get_user_wallet(user)
        transactions = self.get_transaction_history(user)
        
        total_topped_up = sum(
            t.amount for t in transactions 
            if t.transaction_type == "top_up"
        )
        
        total_charged = sum(
            t.amount for t in transactions 
            if t.transaction_type == "charge"
        )
        
        return {
            "current_balance": wallet.balance,
            "total_transactions": len(transactions),
            "total_topped_up": total_topped_up,
            "total_charged": total_charged,
            "wallet_created_at": wallet.created_at if hasattr(wallet, 'created_at') else None
        }