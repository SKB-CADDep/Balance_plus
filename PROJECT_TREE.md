# Дерево проекта Balance_plus

```
Balance_plus-1/
│
├── .github/
│   ├── prompts/
│   ├── scripts/
│   └── workflows/
│
├── .gitignore
├── CONTRIBUTING.md
├── docker-compose.yml
├── PROJECT_TREE.md
├── README.md
├── requirements.txt
│
├── _archive/
│   ├── README.md
│   ├── conftest.py
│   └── pytest.ini
│
├── Parameter Registry Manager/
│   ├── app.py
│   └── registry.db
│
├── GitLAB_pipeline/
│   └── report_MR/
│       ├── .gitlab-ci.yml
│       ├── custom_diff.py
│       └── view_template.yaml
│
├── docs/
│   ├── README.md
│   ├── architecture/
│   ├── methods/
│   ├── specifications/
│   └── materials/
│
├── validation_data/                      # целевое место общих данных (в процессе заполнения)
│   ├── README.md
│   ├── balance/source_data/test_1.json
│   ├── condenser-calculator/strategies/
│   │   ├── berman/
│   │   │   ├── geometrys/
│   │   │   ├── modes/
│   │   │   └── results/
│   │   └── metro_vikers/
│   └── scripts/
│
├── services/
│   ├── balance-orchestrator/
│   │   ├── backend/
│   │   │   ├── pyproject.toml
│   │   │   ├── poetry.lock
│   │   │   ├── app/
│   │   │   └── tests/
│   │   │       ├── conftest.py
│   │   │       └── api/routes/
│   │   │           ├── test_calculations.py
│   │   │           ├── test_projects.py
│   │   │           └── test_tasks.py
│   │   └── frontend/
│   │
│   └── condenser-calculator/
│       └── backend/
│           ├── pyproject.toml
│           ├── README.md
│           ├── app/utils/
│           ├── scripts/
│           └── tests/
│               ├── conftest.py
│               ├── unit/
│               └── validation/berman/
│
└── tests/
    ├── e2e/
    │   └── README.md
    └── validation_data/                  # legacy: будет удалено после полного переноса в `validation_data/`
```

## Описание структуры проекта

### Корневые файлы
- `README.md` — основная документация проекта
- `CONTRIBUTING.md` — руководство по внесению вклада
- `docker-compose.yml` — compose-окружение для сервисов
- `.gitignore` — правила игнорирования файлов для Git
- `PROJECT_TREE.md` — обзор структуры репозитория

### `_archive/`
Архив старых корневых конфигов (`pytest.ini`, `conftest.py`), которые использовались до переноса тестов внутрь сервисов.

### `validation_data/`
Общие данные (JSON и скрипты подготовки) для валидационных тестов.  
Переезд из `tests/validation_data/` выполняется поэтапно (см. пометку `legacy` ниже).

### `services/`
Каждый сервис автономен и содержит **свои тесты** и (при необходимости) **свои скрипты**.

- `services/balance-orchestrator/backend/tests/` — тесты FastAPI backend оркестратора.
- `services/condenser-calculator/backend/tests/` — unit + validation тесты сервиса расчёта конденсатора.
- `services/condenser-calculator/backend/scripts/` — утилиты/отчёты/валидационные скрипты (не `pytest` тесты).

### `tests/`
Тесты уровня монорепозитория:
- `tests/e2e/` — e2e / интеграционные тесты между сервисами
- `tests/validation_data/` — **legacy**: будет удалено после завершения переноса данных в `validation_data/`

