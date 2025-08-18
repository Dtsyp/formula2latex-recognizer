FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание непривилегированного пользователя
RUN groupadd -r mluser && useradd -r -g mluser mluser

# Создание директории для кэша HuggingFace с правильными правами
RUN mkdir -p /home/mluser/.cache/huggingface && \
    chown -R mluser:mluser /home/mluser/.cache && \
    chown -R mluser:mluser /app

USER mluser

# Установка переменной среды для кэша HuggingFace
ENV TRANSFORMERS_CACHE=/home/mluser/.cache/huggingface
ENV HF_HOME=/home/mluser/.cache/huggingface

# Команда по умолчанию
CMD ["python", "worker.py", "--worker-id", "worker-1"]