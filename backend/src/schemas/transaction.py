from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

class TransactionSchema(BaseModel):
    id: UUID
    wallet_id: UUID
    amount: Decimal = Field(..., gt=0)
    timestamp: datetime
    post_balance: Decimal

class TopUpTransactionSchema(TransactionSchema):
    pass

class SpendTransactionSchema(TransactionSchema):
    pass