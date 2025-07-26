"""
Хранилище пользовательских данных для Telegram бота
"""
from typing import Dict, Optional, Set
from dataclasses import dataclass
import json
import aiofiles
import os


@dataclass
class UserSession:
    """Пользовательская сессия"""
    telegram_id: int
    email: Optional[str] = None
    jwt_token: Optional[str] = None
    is_authenticated: bool = False
    current_step: Optional[str] = None  # Для multi-step операций
    temp_data: Optional[Dict] = None  # Временные данные


class UserStorage:
    """Хранилище пользовательских сессий"""
    
    def __init__(self, storage_file: str = "user_sessions.json"):
        self.storage_file = storage_file
        self.sessions: Dict[int, UserSession] = {}
        self.authenticated_users: Set[int] = set()
    
    async def load_sessions(self):
        """Загрузка сессий из файла"""
        if os.path.exists(self.storage_file):
            try:
                async with aiofiles.open(self.storage_file, 'r') as f:
                    data = json.loads(await f.read())
                    for telegram_id_str, session_data in data.items():
                        telegram_id = int(telegram_id_str)
                        session = UserSession(
                            telegram_id=telegram_id,
                            email=session_data.get("email"),
                            jwt_token=session_data.get("jwt_token"),
                            is_authenticated=session_data.get("is_authenticated", False),
                            current_step=session_data.get("current_step"),
                            temp_data=session_data.get("temp_data")
                        )
                        self.sessions[telegram_id] = session
                        if session.is_authenticated:
                            self.authenticated_users.add(telegram_id)
            except Exception as e:
                print(f"Error loading sessions: {e}")
    
    async def save_sessions(self):
        """Сохранение сессий в файл"""
        try:
            data = {}
            for telegram_id, session in self.sessions.items():
                data[str(telegram_id)] = {
                    "email": session.email,
                    "jwt_token": session.jwt_token,
                    "is_authenticated": session.is_authenticated,
                    "current_step": session.current_step,
                    "temp_data": session.temp_data
                }
            
            async with aiofiles.open(self.storage_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def get_session(self, telegram_id: int) -> UserSession:
        """Получение или создание сессии пользователя"""
        if telegram_id not in self.sessions:
            self.sessions[telegram_id] = UserSession(telegram_id=telegram_id)
        return self.sessions[telegram_id]
    
    async def authenticate_user(self, telegram_id: int, email: str, jwt_token: str):
        """Аутентификация пользователя"""
        session = self.get_session(telegram_id)
        session.email = email
        session.jwt_token = jwt_token
        session.is_authenticated = True
        session.current_step = None
        session.temp_data = None
        
        self.authenticated_users.add(telegram_id)
        await self.save_sessions()
    
    async def logout_user(self, telegram_id: int):
        """Выход пользователя из системы"""
        if telegram_id in self.sessions:
            session = self.sessions[telegram_id]
            session.email = None
            session.jwt_token = None
            session.is_authenticated = False
            session.current_step = None
            session.temp_data = None
            
            self.authenticated_users.discard(telegram_id)
            await self.save_sessions()
    
    def is_authenticated(self, telegram_id: int) -> bool:
        """Проверка аутентификации пользователя"""
        return telegram_id in self.authenticated_users
    
    def get_jwt_token(self, telegram_id: int) -> Optional[str]:
        """Получение JWT токена пользователя"""
        if telegram_id in self.sessions:
            return self.sessions[telegram_id].jwt_token
        return None
    
    async def set_current_step(self, telegram_id: int, step: Optional[str]):
        """Установка текущего шага для multi-step операций"""
        session = self.get_session(telegram_id)
        session.current_step = step
        await self.save_sessions()
    
    def get_current_step(self, telegram_id: int) -> Optional[str]:
        """Получение текущего шага"""
        if telegram_id in self.sessions:
            return self.sessions[telegram_id].current_step
        return None
    
    async def set_temp_data(self, telegram_id: int, data: Dict):
        """Установка временных данных"""
        session = self.get_session(telegram_id)
        session.temp_data = data
        await self.save_sessions()
    
    def get_temp_data(self, telegram_id: int) -> Optional[Dict]:
        """Получение временных данных"""
        if telegram_id in self.sessions:
            return self.sessions[telegram_id].temp_data
        return None
    
    async def clear_temp_data(self, telegram_id: int):
        """Очистка временных данных"""
        session = self.get_session(telegram_id)
        session.temp_data = None
        await self.save_sessions()