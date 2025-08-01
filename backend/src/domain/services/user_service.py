from typing import Optional
from uuid import uuid4, UUID

from domain.user import User
from domain.interfaces.repositories import UserRepositoryInterface, WalletRepositoryInterface
from domain.interfaces.services import UserServiceInterface, PasswordServiceInterface


class UserAuthService(UserServiceInterface):
    
    def __init__(
        self, 
        user_repo: UserRepositoryInterface,
        wallet_repo: WalletRepositoryInterface,
        password_service: PasswordServiceInterface
    ):
        self._user_repo = user_repo
        self._wallet_repo = wallet_repo
        self._password_service = password_service
    
    def register_user(self, email: str, password: str) -> User:
        existing_user = self._user_repo.get_by_email(email)
        if existing_user:
            raise ValueError(f"Пользователь с email {email} уже существует")
        
        password_validation = self._password_service.validate_password_strength(password)
        if not password_validation['is_strong']:
            issues = ', '.join(password_validation['issues'])
            raise ValueError(f"Пароль не соответствует требованиям: {issues}")
        
        password_hash = self._password_service.hash_password(password)
        user = self._user_repo.create_user(email, password_hash, "user")
        self._wallet_repo.create_wallet(user.id)
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self._user_repo.get_by_email(email)
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not self._password_service.verify_password(password, user.password_hash):
            return None
        
        return user
    
    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        if not self._password_service.verify_password(old_password, user.password_hash):
            return False
        
        if old_password == new_password:
            raise ValueError("Новый пароль должен отличаться от старого")
        
        password_validation = self._password_service.validate_password_strength(new_password)
        if not password_validation['is_strong']:
            issues = ', '.join(password_validation['issues'])
            raise ValueError(f"Новый пароль не соответствует требованиям: {issues}")
        
        new_password_hash = self._password_service.hash_password(new_password)
        
        updated_user = User(
            id=user.id,
            email=user.email,
            password_hash=new_password_hash,
            role=user.role,
            is_active=user.is_active
        )
        
        self._user_repo.update_user(updated_user)
        return True
    
    def change_email(self, user: User, new_email: str) -> User:
        existing_user = self._user_repo.get_by_email(new_email)
        if existing_user and existing_user.id != user.id:
            raise ValueError(f"Email {new_email} уже занят другим пользователем")
        
        updated_user = User(
            id=user.id,
            email=new_email,
            password_hash=user.password_hash,
            role=user.role,
            is_active=user.is_active
        )
        
        return self._user_repo.update_user(updated_user)
    
    def deactivate_user(self, user: User) -> User:
        updated_user = User(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            is_active=False
        )
        
        return self._user_repo.update_user(updated_user)
    
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self._user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self._user_repo.get_by_email(email)