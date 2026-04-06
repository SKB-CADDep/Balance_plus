FROM python:3.12-slim

# Устанавливаем curl (для healthcheck) и postgresql-client (для pg_isready)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl postgresql-client build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

# Копируем зависимости
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

# Копируем проект
COPY . .

# Лечим переносы строк Windows и выдаем права
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8010

ENTRYPOINT ["/app/entrypoint.sh"]