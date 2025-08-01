from typing import Dict, Any, Type
from functools import lru_cache

from sqlalchemy.orm import Session

from domain.interfaces.repositories import (
    UserRepositoryInterface,
    WalletRepositoryInterface,
    TaskRepositoryInterface,
    MLModelRepositoryInterface
)
from domain.interfaces.services import (
    UserServiceInterface,
    PasswordServiceInterface,
    MessagingServiceInterface
)
from domain.services.user_service import UserAuthService
from domain.services.task_service import TaskManagementService
from domain.services.wallet_service import WalletManagementService

from infrastructure.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyWalletRepository,
    SQLAlchemyTaskRepository,
    SQLAlchemyMLModelRepository
)
from infrastructure.services.password_service import BCryptPasswordService
from infrastructure.messaging import RabbitMQMessagingService
from infrastructure.database import SessionLocal


class DIContainer:
    
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register_singleton(self, interface: Type, implementation: Type):
        self._singletons[interface] = implementation
    
    def register_transient(self, interface: Type, implementation: Type):
        self._instances[interface] = implementation
    
    def get(self, interface: Type):
        if interface in self._singletons:
            return self._get_singleton(interface)
        elif interface in self._instances:
            return self._create_instance(interface)
        else:
            raise ValueError(f"Service {interface.__name__} not registered")
    
    def _get_singleton(self, interface: Type):
        if not hasattr(self, '_singleton_instances'):
            self._singleton_instances = {}
            
        if interface not in self._singleton_instances:
            implementation = self._singletons[interface]
            self._singleton_instances[interface] = self._create_instance_of(implementation)
            
        return self._singleton_instances[interface]
    
    def _create_instance(self, interface: Type):
        implementation = self._instances[interface]
        return self._create_instance_of(implementation)
    
    def _create_instance_of(self, implementation: Type):
        if implementation == SQLAlchemyUserRepository:
            return SQLAlchemyUserRepository(self.get_db_session())
        elif implementation == SQLAlchemyWalletRepository:
            return SQLAlchemyWalletRepository(self.get_db_session())
        elif implementation == SQLAlchemyTaskRepository:
            return SQLAlchemyTaskRepository(self.get_db_session())
        elif implementation == SQLAlchemyMLModelRepository:
            return SQLAlchemyMLModelRepository(self.get_db_session())
        elif implementation == BCryptPasswordService:
            return BCryptPasswordService()
        elif implementation == UserAuthService:
            return UserAuthService(
                user_repo=self.get(UserRepositoryInterface),
                wallet_repo=self.get(WalletRepositoryInterface),
                password_service=self.get(PasswordServiceInterface)
            )
        elif implementation == TaskManagementService:
            return TaskManagementService(
                task_repo=self.get(TaskRepositoryInterface),
                user_repo=self.get(UserRepositoryInterface),
                wallet_repo=self.get(WalletRepositoryInterface),
                ml_model_repo=self.get(MLModelRepositoryInterface),
                messaging_service=self.get(MessagingServiceInterface)
            )
        elif implementation == WalletManagementService:
            return WalletManagementService(
                wallet_repo=self.get(WalletRepositoryInterface)
            )
        elif implementation == RabbitMQMessagingService:
            return RabbitMQMessagingService()
        else:
            raise ValueError(f"Unknown implementation: {implementation.__name__}")
    
    def get_db_session(self) -> Session:
        return SessionLocal()


@lru_cache()
def get_container() -> DIContainer:
    container = DIContainer()
    
    container.register_singleton(UserRepositoryInterface, SQLAlchemyUserRepository)
    container.register_singleton(WalletRepositoryInterface, SQLAlchemyWalletRepository)
    container.register_singleton(TaskRepositoryInterface, SQLAlchemyTaskRepository)
    container.register_singleton(MLModelRepositoryInterface, SQLAlchemyMLModelRepository)
    
    container.register_singleton(PasswordServiceInterface, BCryptPasswordService)
    container.register_singleton(MessagingServiceInterface, RabbitMQMessagingService)
    
    container.register_transient(UserServiceInterface, UserAuthService)
    container.register_transient("TaskManagementService", TaskManagementService)
    container.register_transient("WalletManagementService", WalletManagementService)
    
    return container