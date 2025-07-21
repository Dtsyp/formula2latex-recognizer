from uuid import UUID, uuid4
from typing import Any, Optional
from file import File
from model import MLModel
from wallet import Wallet
import datetime

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
        self._error: Optional[str] = None
        self._status = "pending" # pending | done | error
        self._input = None # Хранение входных данных
        self._output = None # Хранение итоговых данных
        self._credits_charged = model.credit_cost # сколько кредитов будет списано
        self._timestamp = datetime.datetime.utcnow()

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def status(self) -> str:
        return self._status

    @property
    def output(self) -> Optional[str]:
        return self._output

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def credits_charged(self):
        return self._credits_charged

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