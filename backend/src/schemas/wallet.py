from uuid import UUID
from decimal import Decimal
from typing import List
from pydantic import BaseModel
from transaction import TransactionSchema

class WalletSchema(BaseModel):
    id: UUID
    owner_id: UUID
    balance: Decimal
    transactions: List[TransactionSchema] = []