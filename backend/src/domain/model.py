from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any
from uuid import UUID

from domain.file import File

class MLModel(ABC):
    def __init__(self, id: UUID, name: str, credit_cost: Decimal):
        self._id = id
        self._name = name
        self._credit_cost = credit_cost

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def credit_cost(self) -> Decimal:
        """Стоимость за один запрос в модель."""
        return self._credit_cost

    @abstractmethod
    def preprocess(self, file: File) -> Any:
        """Подготовка входных данных."""
        pass

    @abstractmethod
    def predict(self, data: Any) -> str:
        """Прогон данных через модель."""
        pass