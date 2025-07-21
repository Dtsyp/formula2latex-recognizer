from uuid import UUID, uuid4
from wallet import Wallet, Transaction, TopUpTransaction
from task import RecognitionTask
from decimal import Decimal
from file import File
from model import MLModel
from typing import List

# Пользователь
class User:
    def __init__(
            self,
            id: UUID,
            email: str,
            password_hash: str,
            wallet: Wallet
    ):
        self._id = id
        self._email = email
        self._password_hash = password_hash
        self._wallet = wallet
        self._tasks: List[RecognitionTask] = []

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def email(self) -> str:
        return self._email

    @property
    def wallet(self) -> Wallet:
        return self._wallet

    @property
    def tasks(self) -> List[RecognitionTask]:
        # возвращаем копию, чтобы избежать внешних модификаций
        return list(self._tasks)

    def _validate_email(self, email: str) -> None:
        if "@" not in email or len(email) < 5:
            raise ValueError("Некорректный email")

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")

    def get_tasks(self) -> List[RecognitionTask]:
        return self.tasks

    def execute_task(self, file: File, model: MLModel) -> RecognitionTask:
        """
        Создаёт задачу RecognitionTask, выполняет её и сохраняет в историю
        """
        # 1. Создаём новую задачу
        task = RecognitionTask(
            id=uuid4(),
            user_id=self._id,
            file=file,
            model=model
        )

        # 2. Выполняем — внутри обработается ошибка и спишутся кредиты только при успехе
        task.execute(self._wallet)

        # 3. Сохраняем задачу в своей истории
        self._tasks.append(task)

        return task

    def change_email(self, next_email: str) -> bool:
        """
        Сменить email, если новый валиден и отличается от старого.
        """
        self._validate_email(next_email)
        if next_email == self._email:
            return False
        self._email = next_email
        return True

    def change_password(self, prev_password: str, next_password: str) -> bool:
        """
        Сменить пароль: проверяем корректность предыдущего,
        валидируем новый и обновляем хэш.
        """
        # _check_password — приватный метод для сверки хэша
        if not self._check_password(prev_password):
            return False

        self._validate_password(next_password)
        if prev_password == next_password:
            return False

        self._password_hash = self._hash_password(next_password)
        return True

    # Приватные вспомогательные методы:
    def _check_password(self, password: str) -> bool:
        """
        Сравниваем hash(password) с self._password_hash
        """

    def _hash_password(self, password: str) -> str:
        """
        Возвращаем новый хэш
        """

class Admin(User):
    def __init__(
            self,
            id: UUID,
            email: str,
            password_hash: str,
            wallet: Wallet
    ):
        super().__init__(id, email, password_hash, wallet)
        self._role = "admin"

    @property
    def role(self) -> str:
        return self._role

    def top_up_user(self, user: User, amount: Decimal) -> TopUpTransaction:
        """
        Админ может напрямую пополнить баланс любого пользователя
        """
        # Создаём транзакцию пополнения на кошельке пользователя
        txn = user.wallet.top_up(amount)
        return txn

    def view_user_transactions(self, user: User) -> List[Transaction]:
        """
        Посмотреть историю транзакций конкретного пользователя
        """
        return user.wallet.transactions

    def view_all_transactions(self, users: List[User]) -> List[Transaction]:
        """
        Составить общий список транзакций по списку пользователей
        """
        all_txns: List[Transaction] = []
        for u in users:
            all_txns.extend(u.wallet.transactions)

        return all_txns