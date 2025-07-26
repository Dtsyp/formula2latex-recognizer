import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class BotConfig:
    """Конфигурация Telegram бота"""
    token: str
    api_base_url: str
    webhook_url: Optional[str] = None
    webhook_port: int = 8443
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Создание конфигурации из переменных окружения"""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        return cls(
            token=token,
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
            webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL"),
            webhook_port=int(os.getenv("TELEGRAM_WEBHOOK_PORT", "8443")),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )