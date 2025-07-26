"""
Клиент для взаимодействия с REST API
"""
import httpx
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class UserData:
    """Данные пользователя"""
    id: str
    email: str


@dataclass
class WalletData:
    """Данные кошелька"""
    id: str
    balance: str


@dataclass
class ModelData:
    """Данные ML модели"""
    id: str
    name: str
    credit_cost: str
    is_active: bool


@dataclass
class TaskData:
    """Данные задачи"""
    id: str
    status: str
    credits_charged: str
    output_data: Optional[str]
    error_message: Optional[str]
    created_at: str


@dataclass
class TransactionData:
    """Данные транзакции"""
    id: str
    type: str
    amount: str
    post_balance: str
    created_at: str


class APIClient:
    """Клиент для взаимодействия с REST API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def register(self, email: str, password: str) -> Optional[UserData]:
        """Регистрация пользователя"""
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/register",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                return UserData(id=data["id"], email=data["email"])
            return None
        except Exception:
            return None
    
    async def login(self, email: str, password: str) -> Optional[str]:
        """Авторизация пользователя, возвращает JWT токен"""
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                return data["access_token"]
            return None
        except Exception:
            return None
    
    async def get_user_info(self, token: str) -> Optional[UserData]:
        """Получение информации о пользователе"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(f"{self.base_url}/auth/me", headers=headers)
            if response.status_code == 200:
                data = response.json()
                return UserData(id=data["id"], email=data["email"])
            return None
        except Exception:
            return None
    
    async def get_wallet(self, token: str) -> Optional[WalletData]:
        """Получение информации о кошельке"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(f"{self.base_url}/wallet", headers=headers)
            if response.status_code == 200:
                data = response.json()
                return WalletData(id=data["id"], balance=data["balance"])
            return None
        except Exception:
            return None
    
    async def get_transactions(self, token: str) -> List[TransactionData]:
        """Получение истории транзакций"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(f"{self.base_url}/wallet/transactions", headers=headers)
            if response.status_code == 200:
                data = response.json()
                return [
                    TransactionData(
                        id=t["id"],
                        type=t["type"],
                        amount=t["amount"],
                        post_balance=t["post_balance"],
                        created_at=t["created_at"]
                    )
                    for t in data
                ]
            return []
        except Exception:
            return []
    
    async def get_models(self) -> List[ModelData]:
        """Получение списка доступных моделей"""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            if response.status_code == 200:
                data = response.json()
                return [
                    ModelData(
                        id=m["id"],
                        name=m["name"],
                        credit_cost=m["credit_cost"],
                        is_active=m["is_active"]
                    )
                    for m in data
                ]
            return []
        except Exception:
            return []
    
    async def predict(self, token: str, model_id: str, file_content: bytes, filename: str) -> Optional[TaskData]:
        """Создание задачи предсказания"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            encoded_content = base64.b64encode(file_content).decode()
            
            response = await self.client.post(
                f"{self.base_url}/predict",
                headers=headers,
                json={
                    "model_id": model_id,
                    "file_content": encoded_content,
                    "filename": filename
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return TaskData(
                    id=data["id"],
                    status=data["status"],
                    credits_charged=data["credits_charged"],
                    output_data=data.get("output_data"),
                    error_message=data.get("error_message"),
                    created_at=data["created_at"]
                )
            return None
        except Exception:
            return None
    
    async def get_tasks(self, token: str) -> List[TaskData]:
        """Получение истории задач"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(f"{self.base_url}/tasks", headers=headers)
            if response.status_code == 200:
                data = response.json()
                return [
                    TaskData(
                        id=t["id"],
                        status=t["status"],
                        credits_charged=t["credits_charged"],
                        output_data=t.get("output_data"),
                        error_message=t.get("error_message"),
                        created_at=t["created_at"]
                    )
                    for t in data
                ]
            return []
        except Exception:
            return []
    
    async def get_task(self, token: str, task_id: str) -> Optional[TaskData]:
        """Получение информации о конкретной задаче"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(f"{self.base_url}/tasks/{task_id}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                return TaskData(
                    id=data["id"],
                    status=data["status"],
                    credits_charged=data["credits_charged"],
                    output_data=data.get("output_data"),
                    error_message=data.get("error_message"),
                    created_at=data["created_at"]
                )
            return None
        except Exception:
            return None
    
    async def check_api_health(self) -> bool:
        """Проверка доступности API"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Закрытие HTTP клиента"""
        await self.client.aclose()