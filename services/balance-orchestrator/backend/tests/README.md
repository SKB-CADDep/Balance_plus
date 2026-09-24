# Тесты Balance Orchestrator

Запускайте из директории `services/balance-orchestrator/backend`:

```bash
poetry install
poetry run pytest tests/ -v
```

Тесты GitLab-адаптера используют моки и не требуют реального токена или доступа к
заводской сети. Для проверки живого подключения используйте `GET /health/gitlab`.
