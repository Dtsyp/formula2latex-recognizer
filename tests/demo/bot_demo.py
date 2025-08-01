#!/usr/bin/env python3
"""
Демонстрационный скрипт для тестирования Telegram бота
"""
import os
import asyncio
import sys

# Добавляем путь к src для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_bot.config import BotConfig
from telegram_bot.api_client import APIClient


async def test_api_connection():
    """Тестирование подключения к API"""
    print("🔍 Тестирование подключения к API...")
    
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    client = APIClient(api_base_url)
    
    try:
        # Проверяем здоровье API
        is_healthy = await client.check_api_health()
        if is_healthy:
            print(f"✅ API доступен: {api_base_url}")
        else:
            print(f"❌ API недоступен: {api_base_url}")
            return False
        
        # Тестируем получение моделей
        models = await client.get_models()
        print(f"📦 Найдено моделей: {len(models)}")
        for model in models:
            print(f"   • {model.name} - {model.credit_cost} кредитов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False
    finally:
        await client.close()


def check_bot_token():
    """Проверка токена бота"""
    print("🤖 Проверка токена Telegram бота...")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Переменная TELEGRAM_BOT_TOKEN не установлена")
        print("\n💡 Для получения токена:")
        print("1. Найдите @BotFather в Telegram")
        print("2. Отправьте команду /newbot")
        print("3. Следуйте инструкциям")
        print("4. Скопируйте токен и установите переменную:")
        print("   export TELEGRAM_BOT_TOKEN='YOUR_TOKEN_HERE'")
        return False
    
    # Проверяем формат токена
    if ":" not in token or len(token) < 45:
        print("❌ Неверный формат токена")
        return False
    
    print(f"✅ Токен установлен: {token[:10]}...{token[-10:]}")
    return True


async def test_bot_config():
    """Тестирование конфигурации бота"""
    print("⚙️ Тестирование конфигурации бота...")
    
    try:
        config = BotConfig.from_env()
        print(f"✅ Токен бота: {config.token[:10]}...{config.token[-10:]}")
        print(f"✅ API URL: {config.api_base_url}")
        print(f"✅ Webhook URL: {config.webhook_url or 'Не установлен (polling режим)'}")
        print(f"✅ Webhook порт: {config.webhook_port}")
        print(f"✅ Debug режим: {config.debug}")
        return True
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False


async def main():
    """Основная функция демонстрации"""
    print("🚀 ДЕМОНСТРАЦИЯ TELEGRAM БОТА")
    print("=" * 50)
    
    # 1. Проверка токена
    if not check_bot_token():
        print("\n❌ Настройте токен бота и повторите попытку")
        return
    
    print()
    
    # 2. Проверка конфигурации
    if not await test_bot_config():
        print("\n❌ Исправьте конфигурацию и повторите попытку")
        return
    
    print()
    
    # 3. Проверка API
    if not await test_api_connection():
        print("\n❌ Убедитесь, что API сервер запущен:")
        print("   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    print()
    print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print()
    print("📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Запустите API сервер (если еще не запущен):")
    print("   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")
    print()
    print("2. Запустите Telegram бота:")
    print("   python src/telegram_bot/main.py")
    print()
    print("3. Найдите вашего бота в Telegram и отправьте /start")
    print()
    print("🔧 КОМАНДЫ БОТА:")
    print("• /start - Запуск бота и главное меню")
    print("• /help - Справка по использованию")
    print("• /profile - Информация о профиле")
    print("• /balance - Проверка баланса")
    print("• /logout - Выход из аккаунта")
    print()
    print("📸 ФУНКЦИИ:")
    print("• Регистрация и авторизация пользователей")
    print("• Загрузка изображений с формулами")
    print("• Распознавание формул в LaTeX код")
    print("• Управление балансом кредитов")
    print("• Просмотр истории задач и транзакций")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)