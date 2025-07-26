# Formula2LaTeX REST API Documentation

## Обзор

Полнофункциональный REST API для системы распознавания математических формул с JWT аутентификацией, управлением балансом и обработкой задач.

## Архитектура API

### Стек технологий
- **FastAPI** 0.104.1 - современный веб-фреймворк
- **JWT токены** - безопасная аутентификация
- **Pydantic** - валидация данных
- **SQLAlchemy + PostgreSQL** - персистентность данных
- **Comprehensive Testing** - полное покрытие тестами

### Основные компоненты
```
src/api/
├── main.py      # Основное приложение FastAPI
├── auth.py      # JWT аутентификация и авторизация
└── schemas.py   # Pydantic схемы для валидации
```

## API Endpoints

### 🔐 Authentication
Управление пользователями и аутентификация

#### POST `/auth/register`
**Регистрация нового пользователя**
```json
Request Body:
{
  "email": "user@example.com",
  "password": "password123"
}

Response (200):
{
  "id": "uuid",
  "email": "user@example.com"
}
```

#### POST `/auth/login`
**Авторизация пользователя**
```json
Request Body:
{
  "email": "user@example.com", 
  "password": "password123"
}

Response (200):
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

#### GET `/auth/me`
**Получение информации о текущем пользователе**
```
Headers: Authorization: Bearer <token>

Response (200):
{
  "id": "uuid",
  "email": "user@example.com"
}
```

### 💰 Wallet Management
Управление балансом и транзакциями

#### GET `/wallet`
**Получение информации о кошельке**
```
Headers: Authorization: Bearer <token>

Response (200):
{
  "id": "uuid",
  "balance": "100.00"
}
```

#### POST `/wallet/top-up`
**Пополнение кошелька (только для администраторов)**
```json
Headers: Authorization: Bearer <admin_token>
Request Body:
{
  "amount": "50.00"
}

Response (200):
{
  "id": "uuid",
  "type": "top_up",
  "amount": "50.00",
  "post_balance": "150.00",
  "created_at": "2024-01-01T10:00:00Z"
}
```

#### GET `/wallet/transactions`
**Получение истории транзакций**
```
Headers: Authorization: Bearer <token>

Response (200):
[
  {
    "id": "uuid",
    "type": "top_up",
    "amount": "100.00",
    "post_balance": "100.00",
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

### 🤖 ML Models
Управление моделями машинного обучения

#### GET `/models`
**Получение списка доступных ML моделей**
```
Response (200):
[
  {
    "id": "uuid",
    "name": "Basic OCR Model",
    "credit_cost": "2.50",
    "is_active": true
  },
  {
    "id": "uuid", 
    "name": "Advanced LaTeX Model",
    "credit_cost": "5.00",
    "is_active": true
  }
]
```

### 🎯 Predictions
Создание и управление задачами распознавания

#### POST `/predict`
**Создание задачи распознавания формулы**
```json
Headers: Authorization: Bearer <token>
Request Body:
{
  "model_id": "uuid",
  "file_content": "base64_encoded_image",
  "filename": "formula.png"
}

Response (200):
{
  "id": "uuid",
  "status": "done",
  "credits_charged": "5.00",
  "output_data": "\\sum_{i=1}^{n} x_i",
  "error_message": null,
  "created_at": "2024-01-01T10:00:00Z"
}

Response (402) - Insufficient Credits:
{
  "detail": "Insufficient credits"
}
```

### 📋 Tasks
Управление историей задач

#### GET `/tasks`
**Получение истории задач пользователя**
```
Headers: Authorization: Bearer <token>

Response (200):
[
  {
    "id": "uuid",
    "status": "done",
    "credits_charged": "5.00",
    "output_data": "\\sum_{i=1}^{n} x_i",
    "error_message": null,
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

#### GET `/tasks/{task_id}`
**Получение информации о конкретной задаче**
```
Headers: Authorization: Bearer <token>

Response (200):
{
  "id": "uuid",
  "status": "done", 
  "credits_charged": "5.00",
  "output_data": "\\sum_{i=1}^{n} x_i",
  "error_message": null,
  "created_at": "2024-01-01T10:00:00Z"
}
```

### ⚡ Health & Utils
Служебные эндпоинты

#### GET `/`
**Корневой эндпоинт**
```
Response (200):
{
  "message": "Formula2LaTeX Recognizer API",
  "docs": "/docs"
}
```

#### GET `/health`
**Проверка состояния API**
```
Response (200):
{
  "status": "ok",
  "service": "formula2latex-backend"
}
```

## Безопасность

### JWT Authentication
- **Алгоритм**: HS256
- **Время жизни токена**: 30 минут
- **Обновление**: Требуется повторная авторизация

### Защищенные эндпоинты
Все эндпоинты кроме `/auth/register`, `/auth/login`, `/models`, `/health`, `/` требуют JWT токен в заголовке:
```
Authorization: Bearer <jwt_token>
```

### Роли пользователей
- **User**: Стандартный пользователь (регистрация, предсказания, просмотр истории)
- **Admin**: Администратор (+ пополнение балансов)

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешно |
| 400 | Некорректные данные |
| 401 | Не авторизован |
| 402 | Недостаточно кредитов |
| 403 | Нет доступа |
| 404 | Не найдено |
| 422 | Ошибка валидации |

## Примеры использования

### Полный workflow пользователя
```python
import requests
import base64

API_BASE = "http://localhost:8000"

# 1. Регистрация
user_data = {"email": "test@example.com", "password": "password123"}
response = requests.post(f"{API_BASE}/auth/register", json=user_data)
print(f"Registered: {response.json()}")

# 2. Авторизация
response = requests.post(f"{API_BASE}/auth/login", json=user_data)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. Проверка баланса
response = requests.get(f"{API_BASE}/wallet", headers=headers)
print(f"Balance: {response.json()['balance']}")

# 4. Получение моделей
response = requests.get(f"{API_BASE}/models")
models = response.json()
print(f"Available models: {len(models)}")

# 5. Создание предсказания
dummy_image = base64.b64encode(b"image_content").decode()
prediction_data = {
    "model_id": models[0]["id"],
    "file_content": dummy_image,
    "filename": "formula.png"
}
response = requests.post(f"{API_BASE}/predict", json=prediction_data, headers=headers)
print(f"Prediction: {response.json()}")
```

## Тестирование

### Автоматические тесты
```bash
# Запуск всех тестов API
pytest tests/test_api.py -v

# Конкретная группа тестов
pytest tests/test_api.py::TestAuthentication -v
```

### Ручное тестирование
```bash
# Демонстрационный скрипт
python api_demo.py

# Локальный запуск сервера
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Интерактивная документация

### Swagger UI
Доступна по адресу: `http://localhost:8000/docs`
- Интерактивное тестирование всех эндпоинтов
- Автоматическая валидация запросов
- Встроенная аутентификация JWT

### ReDoc
Доступна по адресу: `http://localhost:8000/redoc`
- Красивая документация API
- Детальное описание схем данных

## Развертывание

### Docker
```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Проверка состояния
docker ps
curl http://localhost/health
```

### Локальная разработка
```bash
# Установка зависимостей
pip install -e .

# Запуск PostgreSQL
docker-compose up -d database

# Инициализация БД
python src/infrastructure/init_db.py

# Запуск API сервера
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```