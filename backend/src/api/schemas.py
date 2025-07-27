from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID

class UserRegister(BaseModel):
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

class UserLogin(BaseModel):
    email: str = Field(..., description="Valid email address")
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class WalletResponse(BaseModel):
    id: UUID
    balance: Decimal
    
    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: UUID
    type: str
    amount: Decimal
    post_balance: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True

class TopUpRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount must be positive")

class MLModelResponse(BaseModel):
    id: UUID
    name: str
    credit_cost: Decimal
    is_active: bool
    
    class Config:
        from_attributes = True

class PredictionRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    model_id: UUID
    file_content: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Original filename")

class TaskResponse(BaseModel):
    id: UUID
    status: str
    credits_charged: Decimal
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    detail: str