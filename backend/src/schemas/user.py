from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class UserSchema(BaseModel):
    id: UUID
    email: EmailStr

class AdminSchema(UserSchema):
    role: Literal['admin'] = 'admin'