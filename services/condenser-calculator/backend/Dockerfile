FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.0.1 \
    POETRY_VIRTUALENVS_CREATE=true

# 1. Ускоряем скачивание системных пакетов (зеркало APT для Debian Bookworm)
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    # 2. Ускоряем скачивание самого Poetry (зеркало PyPI)
    && pip install "poetry==$POETRY_VERSION" -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml poetry.lock ./

# 3. Ускоряем скачивание всех библиотек проекта (зеркало Poetry)
RUN poetry config virtualenvs.in-project true \
    && poetry source add --priority=primary mirrors https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && poetry lock \
    && poetry install --only main --no-root

# ========================================== #

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# 4. Зеркало APT для финального образа (чтобы curl и postgresql-client скачались моментально)
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --shell /bin/bash app
WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app . .

RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

USER app
EXPOSE 8010
ENTRYPOINT ["/app/entrypoint.sh"]
