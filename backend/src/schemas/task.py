from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from file import FileSchema
from model import MLModelSchema

class RecognitionTaskSchema(BaseModel):
    id: UUID
    user_id: UUID
    file: FileSchema
    model: MLModelSchema
    status: str = Field(..., pattern=r'^(pending|done|error)$')
    output: Optional[str] = None
    credits_charged: Decimal
    timestamp: datetime