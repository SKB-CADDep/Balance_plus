# condenser-calculator (backend)

Локальный backend сервиса расчёта конденсатора.

## Подключение к PostgreSQL

Приложение и Alembic используют одинаковую конфигурацию. По умолчанию URL
подключения собирается из переменных:

- `POSTGRES_SERVER` (по умолчанию `db`);
- `POSTGRES_PORT` (по умолчанию `5432`);
- `POSTGRES_USER` (по умолчанию `condenser`);
- `POSTGRES_PASSWORD` (по умолчанию `password`);
- `POSTGRES_DB` (по умолчанию `condenser_calc`).

Для Kubernetes достаточно передать эти пять переменных в Deployment или Job.
Переменная `DATABASE_URL`, если задана, имеет приоритет над `POSTGRES_*`.

Если миграции и загрузка справочников выполняются отдельным Kubernetes Job,
в Deployment следует задать:

```text
RUN_MIGRATIONS=false
SEED_DATABASE=false
```

По умолчанию обе операции включены, что сохраняет прежнее поведение Docker
Compose.

## Запуск тестов

Из директории `services/condenser-calculator/backend`:

```bash
python -m pytest
```

Если используете Poetry:

```bash
poetry install
poetry run pytest
```
