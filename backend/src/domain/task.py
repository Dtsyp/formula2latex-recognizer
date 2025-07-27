import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from domain.file import File
from domain.model import MLModel

class RecognitionTask:
    """Задача распознавания формул."""

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
        self._status = "pending"
        self._input = None
        self._output = None
        self._credits_charged = model.credit_cost
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

    def execute(self) -> None:
        """
        Выполнение задачи: предобработка + предсказание
        Логика списания кредитов теперь в User.execute_task
        """
        try:
            preprocessed = self._model.preprocess(self._file)
            result = self._model.predict(preprocessed)
            self._output = result
            self._status = "done"
        except Exception as e:
            self._status = "error"
            self._error = str(e)
            raise

    @property
    def result(self) -> Optional[str]:
        """
        Отдает наружу итоговый LaTeX
        """
        return self._output