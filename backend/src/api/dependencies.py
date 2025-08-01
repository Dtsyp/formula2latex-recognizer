
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

from infrastructure.container import get_container


def get_user_repository() -> UserRepositoryInterface:
    container = get_container()
    return container.get(UserRepositoryInterface)


def get_wallet_repository() -> WalletRepositoryInterface:
    container = get_container()
    return container.get(WalletRepositoryInterface)


def get_task_repository() -> TaskRepositoryInterface:
    container = get_container()
    return container.get(TaskRepositoryInterface)


def get_ml_model_repository() -> MLModelRepositoryInterface:
    container = get_container()
    return container.get(MLModelRepositoryInterface)


def get_password_service() -> PasswordServiceInterface:
    container = get_container()
    return container.get(PasswordServiceInterface)


def get_messaging_service() -> MessagingServiceInterface:
    container = get_container()
    return container.get(MessagingServiceInterface)


def get_user_service() -> UserServiceInterface:
    container = get_container()
    return container.get(UserServiceInterface)


def get_task_service() -> TaskManagementService:
    container = get_container()
    return container.get("TaskManagementService")


def get_wallet_service() -> WalletManagementService:
    container = get_container()
    return container.get("WalletManagementService")