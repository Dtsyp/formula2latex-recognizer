# formula2latex-recognizer
**ML service for handwritten formula recognition and LaTeX code generation**

Проект включает:
- Web‑приложение с регистрацией и авторизацией пользователей
- Управление балансом (пополнение и списание кредитов)
- Загрузку изображений формул через drag & drop или выбор файла
- Асинхронную обработку запросов через RabbitMQ и несколько рабочих процессов
- Генерацию LaTeX‑кода и полученную визуализацию формул
- Историю всех задач с деталями расхода кредитов
- REST‑API для интеграции сторонних сервисов
- Telegram‑бота для взаимодействия через чат

Технологии:
- FastAPI
- React
- PostgreSQL + ORM
- PyTorch / TensorFlow + HuggingFace Transformers (Im2LaTeX / TrOCR)
- RabbitMQ
- Docker & Docker Compose
