from uuid import UUID, uuid4
from decimal import Decimal
from abc import ABC, abstractmethod
import datetime

# Базовый абстрактный класс транзакции
class Transaction(ABC):
    def __init__(
            self,
            id: UUID,
            wallet_id: UUID,
            amount: Decimal,
            timestamp: datetime.datetime,
            post_balance: Decimal
    ):
        self._id: UUID = id
        self._wallet_id: UUID = wallet_id
        self._amount: Decimal = amount # Сумма: при списании < 0, при пополнении > 0
        self._timestamp: datetime.datetime = timestamp # Дата транзакции
        self._post_balance: Decimal = post_balance # Баланс после совершения транзакции

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def wallet_id(self) -> UUID:
        return self._wallet_id

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def timestamp(self) -> datetime.datetime:
        return self._timestamp

    @property
    def post_balance(self) -> Decimal:
        return self._post_balance

    @abstractmethod
    def apply(self, wallet: "Wallet") -> None:
        """
        Применить транзакцию к кошельку:
        - для списания: проверка баланса и уменьшение
        - для пополнения: увеличение
        """
        pass

# Конкретная транзакция пополнения
class TopUpTransaction(Transaction):
    def apply(self, wallet: "Wallet") -> None:
        wallet._balance += self._amount
        wallet._transactions.append(self)

# Конкретная транзакция списания
class SpendTransaction(Transaction):
    def apply(self, wallet: "Wallet") -> None:
        if wallet._balance < self._amount:
            raise RuntimeError("Недостаточно средств для списания")
        wallet._balance -= self._amount
        wallet._transactions.append(self)

# Кошелек пользователя
class Wallet:
    def __init__(
            self,
            id: UUID,
            owner_id: UUID,
            balance: Decimal = Decimal(0)
    ):
        self._id: UUID = id
        self._owner_id: UUID = owner_id
        self._balance: Decimal = balance
        self._transactions: list[Transaction] = []

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def owner_id(self) -> UUID:
        return self._owner_id

    @property
    def balance(self) -> Decimal:
        return self._balance

    @property
    def transactions(self) -> list[Transaction]:
        return list(self._transactions)

    def apply_transaction(self, txn: Transaction) -> None:
        """
        Обобщённый метод для применения любой транзакции
        """
        txn.apply(self)

    def top_up(self, amount: Decimal) -> TopUpTransaction:
        """
        Создаёт транзакцию пополнения
        """
        txn = TopUpTransaction(
            id=uuid4(),
            wallet_id=self._id,
            amount=amount,
            timestamp=datetime.datetime.utcnow(),
            post_balance=self._balance + amount,
        )
        self.apply_transaction(txn)
        return txn

    def spend(self, amount: Decimal) -> SpendTransaction:
        """
        Списывает кредиты — создаёт и применяет транзакцию списания
        """
        txn = SpendTransaction(
            id=uuid4(),
            wallet_id=self._id,
            amount=amount,
            timestamp=datetime.datetime.utcnow(),
            post_balance=self._balance - amount
        )
        self.apply_transaction(txn)
        return txn