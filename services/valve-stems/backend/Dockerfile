# Используем Python 3.12 (совпадает с локальной версией)
FROM python:3.12-slim AS builder

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry==2.1.4

# Копируем файлы зависимостей отдельно (кэширование слоёв Docker)
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости (без dev, без создания venv внутри)
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

# ===== Production stage =====
FROM python:3.12-slim

# Устанавливаем runtime зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копируем код приложения
COPY ./app /app/app

# Копируем миграции
COPY ./alembic.ini /app/alembic.ini

# Копируем и настраиваем entrypoint
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh && sed -i 's/\r$//' /app/entrypoint.sh

# Открываем порт
EXPOSE 5253

# Запуск
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]