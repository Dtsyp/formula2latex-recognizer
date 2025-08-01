# Тесты Formula2LaTeX System

## Структура тестов

### 📁 unit/
**Unit тесты** - тестируют отдельные функции и классы изолированно
- `test_domain.py` - тесты доменных моделей (User, Task, Wallet)
- `test_repositories.py` - тесты репозиториев и работы с БД
- `test_ml_model.py` - тесты ML модели и валидации
- `test_messaging.py` - тесты RabbitMQ интеграции

### 📁 integration/
**Интеграционные тесты** - тестируют взаимодействие между компонентами
- `test_api_integration.py` - тесты REST API endpoints
- `test_ml_worker_integration.py` - тесты ML воркеров с RabbitMQ
- `test_result_processor_integration.py` - тесты обработчика результатов
- `test_telegram_bot_integration.py` - тесты Telegram бота

### 📁 e2e/
**End-to-End тесты** - тестируют полные пользовательские сценарии
- `test_full_ml_pipeline.py` - полный цикл ML обработки
- `test_user_workflow.py` - сценарии пользователя через API
- `test_telegram_workflow.py` - сценарии через Telegram бота

### 📁 demo/
**Демонстрационные скрипты** - примеры использования системы
- `api_demo.py` - демо работы с REST API
- `bot_demo.py` - демо работы с Telegram ботом
- `system_demo.py` - общая демонстрация системы

## Запуск тестов

```bash
# Все тесты
pytest tests/

# Unit тесты
pytest tests/unit/

# Интеграционные тесты  
pytest tests/integration/

# E2E тесты
pytest tests/e2e/

# Демо скрипты
python tests/demo/api_demo.py
```

## Конфигурация

Общая конфигурация тестов находится в `conftest.py` в корне папки tests.