# Telegram Bot Setup Guide

## Быстрый старт

### 1. Получение Telegram Bot Token

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Выберите имя бота (например: "Formula2LaTeX Bot")
   - Выберите username бота (например: "formula2latex_recognizer_bot")
4. Скопируйте полученный токен

### 2. Настройка конфигурации

Отредактируйте файл `.env`:
```bash
# Замените на ваш токен от BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789

# Остальные настройки (опционально)
SECRET_KEY=your-secret-key-change-in-production
# TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
# DEBUG=true
```

### 3. Запуск с Docker

```bash
# Сборка и запуск всех сервисов (включая Telegram бота)
docker-compose up -d

# Проверка состояния
docker-compose ps

# Просмотр логов бота
docker-compose logs -f telegram-bot
```

### 4. Локальный запуск (для разработки)

```bash
# Установка зависимостей
pip install -e .

# Запуск API сервера
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# В другом терминале - запуск бота
export TELEGRAM_BOT_TOKEN="your_token_here"
python src/telegram_bot/main.py
```

## Проверка работы

### Тестирование настроек
```bash
# Проверка конфигурации и API
python bot_demo.py
```

### Использование бота
1. Найдите вашего бота в Telegram по username
2. Отправьте `/start`
3. Пройдите регистрацию или авторизацию
4. Загрузите изображение с формулой
5. Получите LaTeX код!

## Доступные команды

- `/start` - Запуск бота и главное меню
- `/help` - Справка по использованию
- `/profile` - Информация о профиле
- `/balance` - Проверка баланса кредитов
- `/logout` - Выход из аккаунта

## Функции

✅ **Полная интеграция с REST API**
- Регистрация и авторизация
- JWT аутентификация
- Управление балансом
- История задач

✅ **Распознавание формул**
- Загрузка изображений (PNG, JPG, JPEG, GIF)
- Выбор ML моделей
- Получение LaTeX результата
- Автоматическое списание кредитов

✅ **Удобный интерфейс**
- Интерактивные кнопки
- Пошаговые процессы
- Сохранение сессий
- Обработка ошибок

## Структура проекта

```
src/telegram_bot/
├── main.py              # Основной модуль запуска
├── handlers.py          # Обработчики команд и сообщений
├── api_client.py        # HTTP клиент для REST API
├── user_storage.py      # Хранилище пользовательских сессий
└── config.py            # Конфигурация бота
```

## Production настройки

### Webhook режим
```bash
# В .env добавьте:
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
TELEGRAM_WEBHOOK_PORT=8443

# Убедитесь что у вас настроен SSL сертификат
```

### Мониторинг
```bash
# Просмотр логов
docker-compose logs -f telegram-bot

# Restart при необходимости
docker-compose restart telegram-bot
```

## Troubleshooting

### Бот не отвечает
- Проверьте токен в `.env`
- Убедитесь что API сервер запущен
- Проверьте логи: `docker-compose logs telegram-bot`

### Ошибки аутентификации
- Проверьте доступность API: `curl http://localhost:8000/health`
- Очистите сессии: `rm user_sessions.json`

### Проблемы с изображениями
- Максимальный размер: 20MB
- Поддерживаемые форматы: PNG, JPG, JPEG, GIF
- Проверьте баланс кредитов

## Дополнительная документация

Подробная документация доступна в:
- `docs/TELEGRAM_BOT_DOCUMENTATION.md` - полное руководство
- `docs/API_DOCUMENTATION.md` - документация REST API