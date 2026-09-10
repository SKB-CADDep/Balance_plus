#!/bin/bash
set -e

DB_HOST=${POSTGRES_SERVER:-db}
DB_PORT=${POSTGRES_PORT:-5432}
DB_USER=${POSTGRES_USER:-condenser}
DB_PASS=${POSTGRES_PASSWORD:-password}
DB_NAME=${POSTGRES_DB:-condenser_calc}

MAX_TRIES=60
TRIES=0

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

export PGPASSWORD="$DB_PASS"
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

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying Alembic migrations..."
  alembic upgrade head
fi

if [ "${SEED_DATABASE:-true}" = "true" ]; then
  echo "Loading reference data (idempotent)..."
  python seed.py
fi

echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8010 --workers 4
