#!/bin/bash
# Выход при любой ошибке
set -e

# --- Ожидание доступности Базы Данных ---
# Переменные окружения должны быть доступны в контейнере (из docker-compose.yml или .env).
DB_HOST=${POSTGRES_SERVER:-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-postgres}
DB_PASS=${POSTGRES_PASSWORD:-password}
DB_NAME=${POSTGRES_DB:-postgres}

MAX_TRIES=60
TRIES=0

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

# Используем pg_isready из healthcheck'а (требует postgresql-client в образе)
# Установи в Dockerfile, если его нет:
# RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*

PGPASSWORD="$DB_PASS"
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q; do
  TRIES=$((TRIES + 1))
  if [ $TRIES -ge $MAX_TRIES ]; then
    echo "PostgreSQL connection timed out after $MAX_TRIES attempts."
    exit 1
  fi
  >&2 echo "PostgreSQL is unavailable - sleeping ($TRIES/$MAX_TRIES)"
  sleep 1
done

>&2 echo "PostgreSQL is up - proceeding."

# --- Применение миграций Alembic (ЗАКОММЕНТИРОВАНО) ---
# На данном этапе не применяем, т.к. схема создается из дампа
# echo "Applying Alembic migrations..."
# alembic -c /app/alembic.ini upgrade head
# echo "Alembic migrations applied."

echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5253 --workers 4