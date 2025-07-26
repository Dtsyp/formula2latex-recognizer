#!/usr/bin/env python3
"""
Основной модуль Telegram бота для Formula2LaTeX Recognizer
"""
import asyncio
import logging
import os
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Добавляем путь к src для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telegram_bot.config import BotConfig
from telegram_bot.api_client import APIClient
from telegram_bot.user_storage import UserStorage
from telegram_bot.handlers import BotHandlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class Formula2LaTeXBot:
    """Основной класс Telegram бота"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.api_client = APIClient(config.api_base_url)
        self.user_storage = UserStorage()
        self.handlers = BotHandlers(self.api_client, self.user_storage)
        self.application = None
    
    async def initialize(self):
        """Инициализация бота"""
        # Загружаем пользовательские сессии
        await self.user_storage.load_sessions()
        
        # Проверяем доступность API
        if not await self.api_client.check_api_health():
            logger.warning(f"API at {self.config.api_base_url} is not accessible")
        else:
            logger.info(f"API at {self.config.api_base_url} is healthy")
        
        # Создаем приложение бота
        self.application = Application.builder().token(self.config.token).build()
        
        # Регистрируем обработчики команд
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("menu", self.handlers.menu_command))
        self.application.add_handler(CommandHandler("profile", self.handlers.profile_handler))
        self.application.add_handler(CommandHandler("balance", self.handlers.balance_handler))
        self.application.add_handler(CommandHandler("logout", self.handlers.logout_handler))
        
        # Регистрируем обработчики inline кнопок
        self.application.add_handler(CallbackQueryHandler(self.handlers.button_callback))
        
        # Регистрируем обработчики сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.text_message_handler))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handlers.photo_handler))
        self.application.add_handler(MessageHandler(filters.Document.IMAGE, self.handlers.document_handler))
        
        logger.info("Bot handlers registered successfully")
    
    async def start_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Starting bot in polling mode...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        logger.info("Bot is running! Press Ctrl+C to stop.")
        
        # Ждем сигнала остановки
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received stop signal")
        finally:
            await self.shutdown()
    
    async def start_webhook(self):
        """Запуск бота в режиме webhook"""
        if not self.config.webhook_url:
            raise ValueError("Webhook URL is required for webhook mode")
        
        logger.info(f"Starting bot in webhook mode: {self.config.webhook_url}")
        
        await self.application.initialize()
        await self.application.start()
        
        # Устанавливаем webhook
        await self.application.bot.set_webhook(
            url=self.config.webhook_url,
            drop_pending_updates=True
        )
        
        # Запускаем webhook сервер
        await self.application.updater.start_webhook(
            listen="0.0.0.0",
            port=self.config.webhook_port,
            webhook_url=self.config.webhook_url
        )
        
        logger.info(f"Bot webhook is running on port {self.config.webhook_port}")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received stop signal")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Корректное завершение работы бота"""
        logger.info("Shutting down bot...")
        
        # Сохраняем пользовательские сессии
        await self.user_storage.save_sessions()
        
        # Закрываем HTTP клиент
        await self.api_client.close()
        
        # Останавливаем приложение
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        logger.info("Bot shutdown complete")


async def main():
    """Основная функция запуска бота"""
    try:
        # Загружаем конфигурацию
        config = BotConfig.from_env()
        
        # Создаем и инициализируем бота
        bot = Formula2LaTeXBot(config)
        await bot.initialize()
        
        # Запускаем бота
        if config.webhook_url:
            await bot.start_webhook()
        else:
            await bot.start_polling()
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Проверяем переменные окружения
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logger.error("TELEGRAM_BOT_TOKEN environment variable is required")
        print("\nUsage:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        print("export API_BASE_URL='http://localhost:8000'  # optional, defaults to localhost")
        print("python -m telegram_bot.main")
        sys.exit(1)
    
    # Запускаем бота
    asyncio.run(main())