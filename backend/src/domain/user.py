from dataclasses import dataclass
from uuid import UUID
from typing import Optional


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    password_hash: str
    role: str = "user"
    is_active: bool = True
    
    def __post_init__(self):
        self._validate_email(self.email)
        self._validate_role(self.role)
    
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    def is_regular_user(self) -> bool:
        return self.role == "user"
    
    def has_role(self, role: str) -> bool:
        return self.role == role
    
    def _validate_email(self, email: str) -> None:
        if "@" not in email or len(email) < 5:
            raise ValueError("Некорректный email")
    
    def _validate_role(self, role: str) -> None:
        allowed_roles = ["user", "admin"]
        if role not in allowed_roles:
            raise ValueError(f"Недопустимая роль: {role}. Разрешены: {allowed_roles}")


@dataclass(frozen=True)
class Admin(User):
    def __post_init__(self):
        object.__setattr__(self, 'role', 'admin')
        self._validate_email(self.email)
        self._validate_role(self.role)