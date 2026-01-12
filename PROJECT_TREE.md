# Дерево проекта Balance_plus

```
Balance_plus/
│
├── .gitignore
├── README.md
├── CONTRIBUTING.md
├── requirements.txt
│
├── Parameter Registry Manager/
│   ├── app.py
│   └── registry.db
│
├── docs/
│   ├── README.md
│   │
│   ├── architecture/
│   │   ├── C2_Containers.md
│   │   │
│   │   ├── platform/
│   │   │   ├── container-orchestration.md
│   │   │   ├── data-schema-management.md
│   │   │   ├── gitlab.md
│   │   │   ├── message-broker.md
│   │   │   ├── observability.md
│   │   │   └── postgresql-database.md
│   │   │
│   │   └── services/
│   │       ├── api-gateway.md
│   │       ├── condenser_worker.md
│   │       ├── frontend-ide.md
│   │       └── orchestrator.md
│   │
│   └── materials/
│       ├── 1.txt
│       ├── 25.04.21_Балансы.pdf
│       ├── 25.04.25_Пользовательское ТЗ.docx
│       ├── Общая схема.pdf
│       ├── ред_План разработки БАЛАНС+ (для руководства).xlsx
│       ├── ред2_Преза_для_завода_триквел.pptx
│       └── ред4_Для презентации.docx
│
├── services/
│   ├── balance-orchestrator/
│   │   ├── backend/
│   │   │   ├── Dockerfile
│   │   │   ├── pyproject.toml
│   │   │   ├── poetry.lock
│   │   │   │
│   │   │   └── app/
│   │   │       ├── __pycache__/
│   │   │       ├── main.py
│   │   │       │
│   │   │       ├── api/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── __pycache__/
│   │   │       │   │
│   │   │       │   └── routes/
│   │   │       │       ├── __init__.py
│   │   │       │       ├── __pycache__/
│   │   │       │       ├── calculations.py
│   │   │       │       ├── geometries.py
│   │   │       │       ├── health.py
│   │   │       │       ├── projects.py
│   │   │       │       ├── tasks.py
│   │   │       │       └── user.py
│   │   │       │
│   │   │       ├── core/
│   │   │       │   └── gitlab_adapter.py
│   │   │       │
│   │   │       └── schemas/
│   │   │           ├── __init__.py
│   │   │           ├── __pycache__/
│   │   │           ├── calculation.py
│   │   │           ├── geometry.py
│   │   │           └── task.py
│   │   │
│   │   └── frontend/
│   │       ├── .gitignore
│   │       ├── README.md
│   │       ├── index.html
│   │       ├── package.json
│   │       ├── package-lock.json
│   │       ├── tsconfig.json
│   │       ├── tsconfig.app.json
│   │       ├── tsconfig.node.json
│   │       ├── vite.config.ts
│   │       ├── node_modules/
│   │       │
│   │       ├── public/
│   │       │   └── vite.svg
│   │       │
│   │       └── src/
│   │           ├── main.ts
│   │           ├── App.vue
│   │           ├── style.css
│   │           │
│   │           ├── assets/
│   │           │   └── vue.svg
│   │           │
│   │           └── components/
│   │               ├── HelloWorld.vue
│   │               │
│   │               ├── apps/
│   │               │   └── WsaWrapper.vue
│   │               │
│   │               ├── layout/
│   │               │   └── Header.vue
│   │               │
│   │               ├── task-board/
│   │               │   ├── CreateTaskModal.vue
│   │               │   ├── NewTaskCard.vue
│   │               │   └── TaskCard.vue
│   │               │
│   │               └── ui/
│   │                   └── Badge.vue
│   │
│   └── condensers/
│       (пустая директория)
│
├── tests/
│   ├── compare_selection_methods.py
│   ├── generate_report_on_selecting_values.py
│   ├── report_calculation_engine.py
│   ├── report_metrovickers_strategy.py
│   ├── report_module_berman.py
│   ├── report_TPS_module.py
│   ├── test_division_range.py
│   ├── test_metrovickers_strategy.py
│   ├── test_module_berman.py
│   ├── test_selecting_values.py
│   ├── test_table_models.py
│   ├── test_uniconv.py
│   ├── test_VKU_strategy.py
│   ├── validate_exceptions_method.py
│   ├── validate_TPS_module.py
│   └── validate_vku.py
│
└── utils/
    ├── base_for_selection.py
    ├── berman_strategy.py
    ├── calculation_engine.py
    ├── Constants.py
    ├── division_range.py
    ├── exceptions_method.py
    ├── metrovickers_strategy.py
    ├── selection_methods.py
    ├── table_models.py
    ├── TPS_module.py
    ├── uniconv.py
    └── VKU_strategy.py
```

## Описание структуры проекта

### Корневые файлы
- `README.md` - основная документация проекта
- `CONTRIBUTING.md` - руководство по внесению вклада
- `requirements.txt` - зависимости Python
- `.gitignore` - правила игнорирования файлов для Git

### Parameter Registry Manager
Приложение для управления реестром параметров с базой данных SQLite.

### docs/
Документация проекта:
- **architecture/** - архитектурная документация (C4 диаграммы, платформа, сервисы)
- **materials/** - материалы проекта (ТЗ, презентации, схемы)

### services/
Микросервисы проекта:
- **balance-orchestrator/** - оркестратор балансов
  - **backend/** - FastAPI бэкенд (Python, Poetry)
  - **frontend/** - Vue.js фронтенд (TypeScript, Vite)
- **condensers/** - сервисы конденсаторов (пока пустая директория)

### tests/
Тесты для различных модулей:
- Тесты стратегий (Metrovickers, Berman, VKU)
- Тесты модулей (TPS, calculation engine)
- Валидационные тесты
- Отчеты по тестированию

### utils/
Утилиты и модули расчета:
- Стратегии расчета балансов
- Модули конвертации и расчета
- Модели таблиц и константы

