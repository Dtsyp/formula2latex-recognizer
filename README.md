# Formula2LaTeX Recognizer

ML сервис для распознавания рукописных формул и генерации LaTeX кода.

## Описание проекта

Система предоставляет полнофункциональные возможности распознавания формул с веб-приложением:

- Веб-приложение с регистрацией и авторизацией пользователей
- Управление балансом кредитов (пополнение и списание)
- Загрузка изображений формул через drag & drop или выбор файла
- Асинхронная обработка через RabbitMQ с несколькими рабочими процессами
- Генерация LaTeX кода из изображений формул
- Полная история задач с детализацией расхода кредитов
- REST API для интеграции сторонних сервисов
- Telegram бот для взаимодействия через чат

## Стек технологий

**Backend:**
- FastAPI (Python веб-фреймворк)
- PostgreSQL с SQLAlchemy ORM
- RabbitMQ (брокер сообщений)
- JWT аутентификация

**Frontend:**
- React с TypeScript
- Tailwind CSS
- Vite система сборки

**ML обработка:**
- PyTorch/TensorFlow
- HuggingFace Transformers (модель TrOCR)
- Предобработка компьютерного зрения

**Инфраструктура:**
- Docker & Docker Compose
- Nginx (обратный прокси)
- Оркестрация контейнеров

## Требования

- Docker и Docker Compose установлены
- Минимум 8GB RAM доступно
- 10GB свободного места на диске

## Быстрый старт

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd formula2latex-recognizer
```

2. **Создание конфигурации окружения:**
```bash
cd backend
cp .env.example .env
```

Отредактируйте файл `.env` с вашей конфигурацией:
```env
# База данных
POSTGRES_USER=formula_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=formula2latex_db
POSTGRES_HOST=database
POSTGRES_PORT=5432

# JWT
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest

# Telegram Bot (опционально)
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

3. **Сборка и запуск всех сервисов:**
```bash
docker-compose up --build
```

Дождитесь запуска всех сервисов. Первый запуск занимает 5-10 минут из-за загрузки ML моделей.

4. **Инициализация базы данных:**
```bash
docker-compose exec app python src/infrastructure/init_db.py
```

5. **Доступ к приложению:**
- Веб-интерфейс: http://localhost:3000
- Документация API: http://localhost:8000/docs
- Управление RabbitMQ: http://localhost:15672 (guest/guest)

## Архитектура сервисов

Система состоит из нескольких контейнеризованных сервисов:

- **Frontend** (Порт 3000): React веб-приложение
- **Backend** (Порт 8000): FastAPI REST API
- **Database** (Порт 5432): PostgreSQL база данных
- **RabbitMQ** (Порт 5672): Брокер сообщений
- **ML Workers**: Несколько TrOCR процессоров
- **Result Processor**: Обработчик результатов ML

## Тестирование системы

### 1. Регистрация и вход пользователя

1. Перейдите на http://localhost:3000
2. Нажмите "Регистрация" и создайте новый аккаунт
3. Войдите с вашими учетными данными

### 2. Управление кредитами

1. Перейдите на страницу "Кошелек"
2. Добавьте кредиты на ваш счет (любую сумму)
3. Убедитесь, что баланс обновился

### 3. Распознавание формул

1. Перейдите на страницу "Загрузка"
2. Выберите одну из доступных ML моделей
3. Загрузите изображение с математической формулой
4. Дождитесь обработки (обычно 3-5 секунд)
5. Просмотрите сгенерированный LaTeX код

### 4. Отслеживание истории

1. Перейдите на страницу "История"
2. Просмотрите все обработанные формулы
3. Проверьте использование кредитов и временные метки
4. Экспортируйте историю в JSON

### 5. Тестирование API

Протестируйте REST API напрямую:

```bash
# Получение токена аутентификации
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your_password"}'

# Загрузка формулы (замените TOKEN на полученный токен)
curl -X POST "http://localhost:8000/predict/upload" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@path/to/formula.png" \
  -F "model_id=your_model_id"
```

## Мониторинг и логи

Мониторинг статуса сервисов и логов:

```bash
# Проверка статуса сервисов
docker-compose ps

# Просмотр логов
docker-compose logs app          # Логи backend
docker-compose logs frontend     # Логи frontend
docker-compose logs ml-worker-1  # Логи ML воркера
docker-compose logs rabbitmq     # Логи брокера сообщений

# Отслеживание логов в реальном времени
docker-compose logs -f app
```

## Разработка

### Запуск сервисов по отдельности

Для разработки можно запускать сервисы индивидуально:

```bash
# Только база данных
docker-compose up database rabbitmq

# Разработка backend
cd backend
pip install -e .
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Разработка frontend
cd frontend
npm install
npm run dev
```

### Управление базой данных

```bash
# Прямой доступ к базе данных
docker-compose exec database psql -U formula_user -d formula2latex_db

# Выполнение миграций
docker-compose exec app alembic upgrade head

# Создание новой миграции
docker-compose exec app alembic revision --autogenerate -m "Описание"
```

### Тестирование

Запуск тестового набора:

```bash
# Модульные тесты
docker-compose exec app pytest tests/unit/

# Интеграционные тесты
docker-compose exec app pytest tests/integration/

# End-to-end тесты
docker-compose exec app pytest tests/e2e/
```

## Развертывание в продакшн

Для продакшн развертывания:

1. Обновите переменные окружения в `.env`
2. Настройте SSL сертификаты
3. Настройте мониторинг и логирование
4. Настройте стратегии резервного копирования базы данных
5. Масштабируйте ML воркеры в зависимости от нагрузки

## Устранение неполадок

### Частые проблемы

**ML воркеры не запускаются:**
- Проверьте доступную память (модели требуют ~2GB RAM каждая)
- Убедитесь в подключении к RabbitMQ

**Ошибки подключения к базе данных:**
- Убедитесь, что контейнер PostgreSQL запущен
- Проверьте учетные данные базы данных в `.env`

**Frontend не загружается:**
- Убедитесь, что backend доступен на порту 8000
- Проверьте консоль браузера на ошибки

**Таймауты обработки:**
- Увеличьте количество воркеров в docker-compose.yml
- Мониторьте статус очереди RabbitMQ

### Оптимизация производительности

- Масштабирование ML воркеров: Добавьте больше сервисов `ml-worker-X`
- Оптимизация базы данных: Добавьте индексы для частых запросов
- Кэширование: Внедрите Redis для управления сессиями
- Балансировка нагрузки: Используйте несколько экземпляров backend

## Документация API

Полная документация API доступна по адресу http://localhost:8000/docs при запущенном backend.

Ключевые эндпоинты:
- `POST /auth/register` - Регистрация пользователя
- `POST /auth/login` - Аутентификация пользователя
- `POST /predict/upload` - Распознавание формул
- `GET /tasks` - История задач
- `GET /models` - Доступные ML модели
