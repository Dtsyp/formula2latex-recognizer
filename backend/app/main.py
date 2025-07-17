from uuid import UUID, uuid4
from decimal import Decimal
from typing import List, Optional, Any
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
        self._amount: Decimal = amount
        self._timestamp: datetime.datetime = timestamp
        self._post_balance: Decimal = post_balance

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
        Создаёт транзакцию пополнения, сразу одобряет и применяет её
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

class File:
    def __init__(self, path: str, content_type: str):
        self._path = path
        self._content_type = content_type
        self._validate()

    # Валидация загруженного файла
    def _validate(self) -> None:
        if not self._content_type.startswith('image/'):
            raise ValueError("Поддерживаются только изображения")
        # можно добавить проверку размера, разрешения и тп

    @property
    def path(self) -> str:
        return self._path

# Единый интерфейс моделей
class MLModel(ABC):
    def __init__(self, id: UUID, name: str, credit_cost: Decimal):
        self._id = id
        self._name = name
        self._credit_cost = credit_cost

    @property
    def credit_cost(self) -> Decimal:
        """
        Стоимость (сколько будет списано) за один запрос в модель
        """
        return self._credit_cost

    @abstractmethod
    def preprocess(self, file: File) -> Any:
        """
        Подготовка входных данных
        """
        pass

    @abstractmethod
    def predict(self, data: Any) -> str:
        """
        Прогон данных через модель
        """
        pass

# Пример с конкретной моделью
# class FormulaCRNNModel(MLModel):
#     def preprocess(self, file: File) -> Image:
#         # загружаем картинку, конвертируем в grayscale, ресайз
#         pass
#
#     def predict(self, data: Image) -> str:
#         # прогон через CRNN, декодирование CTC → строка LaTeX
#         pass

# Пользовательская задача, хранит входные данные, результат и обращается к моделям
class RecognitionTask:
    def __init__(
            self,
            id: UUID,
            user_id: UUID,
            file: File,
            model: MLModel
    ):
        self._id = id
        self._user_id = user_id
        self._file = file
        self._model = model
        self._status = "pending" # pending | done | error
        self._input = None # Хранение входных данных
        self._output = None # Хранение итоговых данных
        self._credits_charged = model.credit_cost # сколько кредитов будет списано
        self._timestamp = datetime.datetime.utcnow()

    def execute(self, wallet: Wallet) -> None:
        """
        Выполнение задачи: предобработка + предсказание
        Списываем кредиты только если оба этапа прошли без ошибок
        В случае ошибки сохраняем её и оставляем баланс нетронутым
        """
        try:
            # Проверка достаточного баланса заранее
            if wallet.balance < self._credits_charged:
                raise RuntimeError("Недостаточно кредитов")

            # Этапы выполнения модели
            preprocessed = self._model.preprocess(self._file)
            result = self._model.predict(preprocessed)

        except Exception as e:
            # Если что-то пошло не так — фиксируем ошибку и статус
            self._status = "error"
            self._error = str(e)
            return

        # Всё прошло успешно — списываем кредиты и сохраняем результат
        wallet.spend(self._credits_charged)
        self._output = result
        self._status = "done"

    @property
    def result(self) -> Optional[str]:
        """
        Отдает наружу итоговый LaTeX
        """
        return self._output


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
        Посмотреть историю транзакций конкретного пользователя.
        """
        return user.wallet.transactions

    def view_all_transactions(self, users: List[User]) -> List[Transaction]:
        """
        Составить общий список транзакций по списку пользователей
        """
        all_txns: List[Transaction] = []
        for u in users:
            all_txns.extend(u.wallet.transactions)