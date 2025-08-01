# ML Модуль для распознавания формул

Этот модуль содержит ML компоненты для распознавания математических формул и конвертации их в LaTeX код.

## Компоненты

### 1. ML Модель (`model.py`)
- Использует TrOCR (Transformer-based OCR) от Microsoft
- Поддерживает конвертацию изображений формул в LaTeX
- Включает валидацию входных изображений
- Singleton pattern для эффективного использования памяти

### 2. RabbitMQ Мессенджер (`messaging.py`)
- Настройка exchanges и очередей
- Публикация задач и получение результатов
- Dead Letter Queue для обработки ошибок
- Конфигурируемые таймауты и QoS

### 3. ML Воркеры (`worker.py`)
- Получение задач из RabbitMQ
- Валидация данных изображений
- Выполнение предикта через ML модель
- Отправка результатов обратно в очередь
- Graceful shutdown по сигналам

### 4. Менеджер воркеров (`start_workers.py`)
- Запуск нескольких воркеров параллельно
- Мониторинг состояния воркеров
- Логирование и управление процессами
- Автоматический перезапуск при сбоях

## Установка и запуск

### Локальная установка
```bash
cd ml/
pip install -r requirements.txt
```

### Запуск одного воркера
```bash
python worker.py --worker-id worker-1
```

### Запуск нескольких воркеров
```bash
python start_workers.py --workers 3
```

### Docker запуск
```bash
# Из корневой директории проекта
docker-compose -f backend/docker-compose.yml up ml-worker-1 ml-worker-2 ml-worker-3
```

## Переменные окружения

- `RABBITMQ_HOST` - хост RabbitMQ (по умолчанию: localhost)
- `RABBITMQ_PORT` - порт RabbitMQ (по умолчанию: 5672)
- `RABBITMQ_USERNAME` - имя пользователя (по умолчанию: guest)
- `RABBITMQ_PASSWORD` - пароль (по умолчанию: guest)
- `RABBITMQ_VHOST` - виртуальный хост (по умолчанию: /)

## Архитектура очередей

### Exchanges
- `formula_tasks` - для распределения задач
- `formula_results` - для сбора результатов

### Queues
- `formula_recognition_queue` - основная очередь задач
- `formula_results_queue` - очередь результатов
- `formula_dead_letter_queue` - очередь для проблемных сообщений

### Routing Keys
- `formula.recognition` - для задач распознавания
- `formula.result` - для результатов

## Формат сообщений

### Задача (Task)
```json
{
  "task_id": "uuid",
  "user_id": "user_uuid", 
  "image_data": "base64_encoded_image",
  "filename": "formula.png",
  "model_id": "model_id",
  "timestamp": 1234567890.123
}
```

### Результат (Result)
```json
{
  "task_id": "uuid",
  "user_id": "user_uuid",
  "worker_id": "worker-1",
  "timestamp": "2024-01-01T12:00:00",
  "processing_time": 2.5,
  "success": true,
  "latex_code": "x^2 + y^2 = r^2",
  "confidence": 0.95,
  "error": null,
  "image_info": {
    "width": 300,
    "height": 100,
    "format": "PNG"
  }
}
```

## Мониторинг

### Логи воркеров
Воркеры выводят подробные логи включая:
- Статус подключения к RabbitMQ
- Время загрузки ML модели
- Детали обработки каждой задачи
- Ошибки и исключения

### Метрики RabbitMQ
Доступны через веб-интерфейс: http://localhost:15672
- Количество сообщений в очередях
- Скорость обработки
- Количество подключенных воркеров