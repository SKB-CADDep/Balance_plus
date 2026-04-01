FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.1.4
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN useradd --shell /bin/bash app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY --chown=app:app ./app /app/app
COPY --chown=app:app ./alembic.ini /app/alembic.ini
COPY --chown=app:app ./entrypoint.sh /app/entrypoint.sh
RUN chmod 755 /app/entrypoint.sh && sed -i 's/\r$//' /app/entrypoint.sh
EXPOSE 5253
USER app
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
