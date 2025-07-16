from uuid import UUID
from decimal import Decimal
from typing import List, Optional

class Transaction:
    pass

class RecognitionTask:
    pass

class File:
    pass

class Wallet:
    def __init__(
            self,
            id: UUID,
            owner_id: UUID,
            balance: Decimal
    ):
        self._id = id
        self._owner_id = owner_id
        self._balance = balance
        self._transactions: List[Transaction] = []

    # открытые свойства для чтения
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
    def transactions(self) -> List[Transaction]:
        return list(self._transactions)

class User:
    def __init__(
            self,
            id: UUID,
            email: str,
            password_hash: str,
            balance: Decimal
    ):
        self._id = id
        self._email = email
        self._password_hash = password_hash
        self._balance = balance
        self._tasks: List[RecognitionTask] = []

    # открытые свойства для чтения
    @property
    def id(self) -> UUID:
        return self._id

    @property
    def email(self) -> str:
        return self._email

    @property
    def balance(self) -> Decimal:
        return self._balance

    @property
    def tasks(self) -> List[RecognitionTask]:
        return list(self._tasks)

    def _validate_email(self) -> None:
        """
        валидация email
        """

    def _validate_password(self) -> None:
        """
        валидация password
        """

    # публичные методы
    def get_history(self) -> List[RecognitionTask]:
        """
        Возвращает историю всех задач пользователя
        """
        return self.tasks

    def execute_task(self, file: File) -> RecognitionTask:
        """
        Инициирует задачу, списывает кредиты,
        добавляет в self._tasks и возвращает саму задачу
        """

    def top_up(self, amount: Decimal) -> Wallet:
        """
        Пополняет баланс на amount, создаёт и возвращает Wallet
        """

    def change_email(self, next_email: str) -> bool:
        """
        Изменяет email, нужно будет проверить что бы они не совпадали (self.email != next_email)
        """

    def change_password(self, prev_password: str, next_password: str) -> bool:
        """
        Изменяет пароль, проверяем, что prev_password корректный
        и сравниваем чтобы не совпадал с next_password,
        обновить password_hash
        """