# Тесты Formula2LaTeX System

## Структура тестов

### unit/
Unit тесты - тестируют отдельные функции и классы изолированно
- `test_domain.py` - тесты доменных моделей (User, Admin, Wallet, Transactions)
- `test_domain_services.py` - тесты доменных сервисов (UserAuthService, WalletManagementService)
- `test_repositories.py` - тесты репозиториев и работы с БД
- `test_ml_model.py` - тесты ML модели и валидации

### integration/
Интеграционные тесты - тестируют взаимодействие между компонентами
- `test_api_integration.py` - тесты REST API endpoints
- `test_ml_worker_integration.py` - тесты ML воркеров с RabbitMQ
- `test_system_integration.py` - тесты полной интеграции системы

### e2e/
End-to-End тесты - тестируют полные пользовательские сценарии
- `test_api_workflow.py` - сценарии пользователя через REST API
- `test_telegram_workflow.py` - сценарии через Telegram бота

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

# Конкретный файл тестов
pytest tests/unit/test_domain.py -v

# Тесты с покрытием
pytest tests/ --cov=backend/src --cov-report=html
```

## Конфигурация

Общая конфигурация тестов находится в `conftest.py` в корне папки tests.

## Покрытие тестами

Текущие unit тесты покрывают:
- Доменные модели (User, Admin, Wallet, Transactions)
- Доменные сервисы (UserAuthService, WalletManagementService)  
- Репозитории (SQLAlchemy implementations)
- ML модель (с моками PyTorch)