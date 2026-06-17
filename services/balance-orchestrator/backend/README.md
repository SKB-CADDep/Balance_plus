# Balance Orchestrator (Backend)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![GitLab API](https://img.shields.io/badge/python--gitlab-FCA121?style=for-the-badge&logo=gitlab)
![Vue.js](https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D)

Бэкенд центрального микросервиса **Balance+ IDE**. Выполняет роль API Gateway и интеграционного слоя между клиентским интерфейсом (Vue.js), репозиториями GitLab и изолированными математическими воркерами.

## Архитектура и назначение

Оркестратор не выполняет тяжелых математических расчетов (они делегируются в микросервисы `condenser-calculator` и `valve-stems`). Его главные задачи:
1. **Интеграция с GitLab**: Аутентификация, получение списка проектов, задач (Issues) и управление ветками (Branches).
2. **Маршрутизация расчетов**: Прием данных от фронтенда и передача их соответствующим математическим ядрам.
3. **Генерация артефактов**: Автоматическое создание Merge Requests (MR) с результатами расчетов.
4. **BFF (Backend-for-Frontend)**: Подготовка и форматирование конфигурационных справочников для удобной отрисовки в UI.

> **[ENGINEERING CONTEXT] Архитектура "Git-as-a-Database":**
> В этом микросервисе вы практически не найдете работы с классическими базами данных (PostgreSQL) для сохранения прогресса задач. Состояние системы хранится напрямую в репозиториях GitLab. 
> - **Задача инженера** = GitLab Issue.
> - **Рабочее пространство** = Git Branch.
> - **Сохранение (Save)** = Commit JSON-файлов в папку `/current/`.
> - **Отправка на ревью** = Создание Merge Request.
> Такая архитектура гарантирует 100% версионирование всех инженерных расчетов и избавляет от рассинхронизации между БД и реальным кодом.

---

## Структура проекта

Кодовая база разделена на серверную часть (FastAPI) и клиентский интерфейс (Vue.js):

```text
📁 balance-orchestrator/
│   ├── 📁 backend/                 # [API GATEWAY & ИНТЕГРАЦИЯ]
│   │   ├── 📁 app/
│   │   │   ├── 📁 api/
│   │   │   │   ├── 📁 routes/      # HTTP-эндпоинты
│   │   │   │   │   ├── 🐍 __init__.py
│   │   │   │   │   ├── 🐍 calculations.py
│   │   │   │   │   ├── 🐍 config.py
│   │   │   │   │   ├── 🐍 geometries.py
│   │   │   │   │   ├── 🐍 health.py
│   │   │   │   │   ├── 🐍 projects.py
│   │   │   │   │   ├── 🐍 tasks.py
│   │   │   │   │   └── 🐍 user.py
│   │   │   │   └── 🐍 __init__.py
│   │   │   ├── 📁 core/
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   └── 🐍 gitlab_adapter.py  # Мост для работы с GitLab API
│   │   │   ├── 📁 schemas/         # Pydantic модели
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 calculation.py
│   │   │   │   ├── 🐍 geometry.py
│   │   │   │   └── 🐍 task.py
│   │   │   └── 🐍 main.py
│   │   ├── 📁 tests/               # Автотесты (Tavern и Pytest)
│   │   │   ├── 📁 api/
│   │   │   │   └── 📁 routes/
│   │   │   │       ├── ⚙️ __group__.yml
│   │   │   │       ├── 🐍 test_berman_demo_calc.py
│   │   │   │       ├── 🐍 test_calculations.py
│   │   │   │       ├── ⚙️ test_calculations.tavern.yaml
│   │   │   │       ├── 🐍 test_projects.py
│   │   │   │       └── 🐍 test_tasks.py
│   │   │   ├── 📁 unit/
│   │   │   │   └── ⚙️ __group__.yml
│   │   │   ├── 🐍 conftest.py
│   │   │   └── 📖 README.md
│   │   ├── 📄 .env.example
│   │   ├── 🐳 Dockerfile
│   │   ├── 🔒 poetry.lock
│   │   ├── 📦 pyproject.toml
│   │   └── ⚙️ pytest.ini
│   │
│   ├── 📁 frontend/                # [ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС]
│   │   ├── 📁 .vscode/
│   │   │   └── 📋 extensions.json
│   │   ├── 📁 public/
│   │   │   └── 🖼️ vite.svg
│   │   ├── 📁 src/
│   │   │   ├── 📁 assets/
│   │   │   │   └── 🖼️ vue.svg
│   │   │   ├── 📁 components/
│   │   │   │   ├── 📁 apps/
│   │   │   │   │   └── 📄 WsaWrapper.vue
│   │   │   │   ├── 📁 layout/
│   │   │   │   │   └── 📄 Header.vue
│   │   │   │   ├── 📁 task-board/  # Компоненты Kanban-доски
│   │   │   │   │   ├── 📄 CreateTaskModal.vue
│   │   │   │   │   ├── 📄 NewTaskCard.vue
│   │   │   │   │   └── 📄 TaskCard.vue
│   │   │   │   ├── 📁 ui/
│   │   │   │   │   └── 📄 Badge.vue
│   │   │   │   └── 📄 HelloWorld.vue
│   │   │   ├── 📄 App.vue
│   │   │   ├── 📜 main.ts
│   │   │   └── 🎨 style.css
│   │   ├── 🙈 .gitignore
│   │   ├── 🐳 Dockerfile
│   │   ├── 🌐 index.html
│   │   ├── 📄 nginx.conf
│   │   ├── 📋 package-lock.json
│   │   ├── 📋 package.json
│   │   ├── 📖 README.md
│   │   ├── 📋 tsconfig.app.json
│   │   ├── 📋 tsconfig.json
│   │   ├── 📋 tsconfig.node.json
│   │   └── 📜 vite.config.ts
│   │
│   └── ⚙️ docker-compose.yaml      # Локальный запуск сервиса
```

---

## Предварительные требования и `.env`

Для локального запуска оркестратора необходимо настроить связь с инстансом GitLab. Создайте файл `.env` в корне директории `backend/`:

```env
# Пример .env файла
GITLAB_URL=https://gitlab.com # или URL вашего корпоративного GitLab
GITLAB_PRIVATE_TOKEN=<your_personal_access_token>
SECRET_KEY=<your_secret_key_here>
DEBUG=True
```

> **[!WARNING] Безопасность токенов**
> Никогда не коммитьте свой `GITLAB_PRIVATE_TOKEN` в систему контроля версий. Для локальной разработки сгенерируйте `Personal Access Token` в настройках своего профиля GitLab с правами `api`.

---

## Руководство по локальному запуску

Все команды ниже выполняются из директории бэкенда:  
`services/balance-orchestrator/backend/`

### 1. Установка зависимостей (Poetry)
Разрешение и установка пакетов:
```bash
poetry install
```

### 2. Запуск сервера API (FastAPI)
Запустите бэкенд Оркестратора. Согласно глобальной матрице портов Balance+ IDE, данный сервис **жестко привязан к порту 8005**:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

 **Успех!** Интерактивная документация (Swagger UI) доступна по адресу:  
 **http://localhost:8005/docs**

---

## Взаимодействие с другими сервисами (CORS)

Так как Оркестратор является шлюзом, он принимает запросы от фронтенда и отправляет их дальше. Убедитесь, что остальные части системы запущены на правильных портах:

| Сервис / Модуль | Компонент | Локальный URL / Порт |
| :--- | :--- | :--- |
| **Balance Orchestrator** | Frontend (UI) | `http://localhost:3000` |
| **Balance Orchestrator** | API Backend (Текущий) | `http://localhost:8005` |
| **Condenser Calculator** | API Backend | `http://localhost:8010` |
| **Valve Stems** | API Backend | `http://localhost:5253` |

---

## Качество кода и тесты

В проекте настроено комплексное тестирование. Для проверки работоспособности мостов (адаптеров) GitLab, Pydantic-схем и роутов выполните:
```bash
poetry run pytest
```
