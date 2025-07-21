from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

class MLModelSchema(BaseModel):
    id: UUID
    name: str
    credit_cost: Decimal = Field(..., gt=0)