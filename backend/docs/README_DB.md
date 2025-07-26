# База данных formula2latex-recognizer

## Обзор

Проект интегрирован с PostgreSQL с использованием SQLAlchemy ORM и Alembic для миграций.

## Структура базы данных

### Таблицы

1. **users** - Пользователи системы
   - `id` (UUID, PK)
   - `email` (String, unique)
   - `password_hash` (String)
   - `role` (Enum: user, admin)
   - `created_at`, `updated_at`

2. **wallets** - Кошельки пользователей
   - `id` (UUID, PK)
   - `owner_id` (UUID, FK → users.id)
   - `balance` (Decimal)
   - `created_at`, `updated_at`

3. **transactions** - История транзакций
   - `id` (UUID, PK)
   - `wallet_id` (UUID, FK → wallets.id)
   - `type` (Enum: top_up, spend)
   - `amount` (Decimal)
   - `post_balance` (Decimal)
   - `created_at`

4. **ml_models** - Доступные ML модели
   - `id` (UUID, PK)
   - `name` (String)
   - `credit_cost` (Decimal)
   - `is_active` (Integer)
   - `created_at`, `updated_at`

5. **files** - Загруженные файлы
   - `id` (UUID, PK)
   - `path` (String)
   - `content_type` (String)
   - `original_filename` (String)
   - `size` (Integer)
   - `created_at`

6. **tasks** - Задачи распознавания
   - `id` (UUID, PK)
   - `user_id` (UUID, FK → users.id)
   - `file_id` (UUID, FK → files.id)
   - `model_id` (UUID, FK → ml_models.id)
   - `status` (Enum: pending, in_progress, done, error)
   - `credits_charged` (Decimal)
   - `input_data`, `output_data` (Text)
   - `error_message` (Text)
   - `created_at`, `updated_at`

## Установка и настройка

### 1. Установка зависимостей

```bash
pip install -e .
```

### 2. Настройка переменных окружения

Создайте файл `.env` или используйте существующий:

```env
DATABASE_URL=postgresql://app_user:SuperSecretPass123@database:5432/app_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=SuperSecretPass123
POSTGRES_DB=app_db
```

### 3. Запуск базы данных

```bash
# Запуск PostgreSQL через Docker
docker-compose up -d database
```

### 4. Инициализация БД с демо данными

```bash
# Создание таблиц и заполнение демо данными
python src/infrastructure/init_db.py
```

## Тестирование

### Быстрое тестирование без БД

```bash
# Тестирование доменных моделей и импортов
python test_system.py
```

### Полное тестирование с БД

```bash
# Запуск всех тестов (требует PostgreSQL)
pytest tests/ -v
```

## Демо данные

После инициализации создаются:

### Пользователи
- **Админ**: `admin@formula2latex.com` / `admin123`
- **Пользователь**: `user@formula2latex.com` / `user123` (100.00 кредитов)

### ML Модели
1. **Basic OCR Model** - 2.50 кредитов
2. **Advanced LaTeX Model** - 5.00 кредитов  
3. **Premium Deep Learning Model** - 10.00 кредитов

## Основной функционал

### Создание пользователя

```python
from infrastructure.repositories import UserRepository
from infrastructure.database import SessionLocal

db = SessionLocal()
user_repo = UserRepository(db)

# Создание обычного пользователя
user = user_repo.create_user("new@example.com", "password123")

# Создание админа
admin = user_repo.create_user("admin@example.com", "password123", role="admin")
```

### Работа с кошельком

```python
from infrastructure.repositories import WalletRepository

wallet_repo = WalletRepository(db)
wallet = wallet_repo.get_by_owner_id(user.id)

# Пополнение баланса
top_up_txn = wallet.top_up(Decimal("50.00"))
wallet_repo.add_transaction(top_up_txn)
wallet_repo.update_balance(wallet.id, wallet.balance)

# Списание кредитов
spend_txn = wallet.spend(Decimal("10.00"))
wallet_repo.add_transaction(spend_txn)
wallet_repo.update_balance(wallet.id, wallet.balance)
```

### Создание ML модели

```python
from infrastructure.repositories import MLModelRepository

model_repo = MLModelRepository(db)
model = model_repo.create_model("Custom Model", Decimal("7.50"))
```

## Миграции

### Создание новой миграции

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Применение миграций

```bash
alembic upgrade head
```

### Откат миграций

```bash
alembic downgrade -1  # на одну версию назад
alembic downgrade base  # к начальному состоянию
```

## Архитектурные принципы

1. **Domain-Driven Design** - Доменные модели отделены от инфраструктуры
2. **Repository Pattern** - Абстракция доступа к данным
3. **Dependency Injection** - Передача зависимостей через конструкторы
4. **Transaction Management** - Контроль транзакций на уровне репозиториев

## Структура файлов

```
backend/
├── src/
│   ├── domain/               # Доменные модели
│   │   ├── user.py
│   │   ├── wallet.py
│   │   ├── task.py
│   │   ├── file.py
│   │   └── model.py
│   ├── infrastructure/       # Инфраструктурный слой
│   │   ├── database.py       # Подключение к БД
│   │   ├── models.py         # SQLAlchemy модели
│   │   ├── repositories.py   # Репозитории
│   │   └── init_db.py        # Инициализация БД
│   └── schemas/              # Pydantic схемы
├── tests/                    # Тесты
│   ├── conftest.py
│   └── test_repositories.py
├── alembic/                  # Миграции
└── pyproject.toml            # Зависимости и конфигурация
```

## Troubleshooting

### Ошибки подключения к БД

1. Убедитесь, что PostgreSQL запущен
2. Проверьте правильность переменных окружения
3. Проверьте доступность порта 5432

### Ошибки миграций

1. Убедитесь, что БД создана
2. Проверьте alembic.ini конфигурацию
3. Убедитесь в правильности импортов в alembic/env.py

### Ошибки тестов

1. Убедитесь, что все зависимости установлены
2. Проверьте импорты модулей
3. Для тестов с БД убедитесь в доступности PostgreSQL