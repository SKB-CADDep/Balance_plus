# **Balance+ IDE** 🚀

[![Статус](https://img.shields.io/badge/Status-Advanced_Beta-orange)](#)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-brightgreen?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-brightgreen?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitLab%20%7C%20GitHub-blue)](#)

**Balance+ IDE** – это специализированная интегрированная среда разработки (IDE) для инженеров-расчётчиков. Система реализует концепцию **"Engineering as Code"**, автоматизируя тяжелые математические расчеты (конденсаторы, штоки клапанов) и используя GitLab как единый источник правды.

> **Статус проекта:** Продвинутая Бета (Активная разработка). Проект готовится к внедрению в enterprise-среду закрытого контура. CI-пайплайны настроены на строгий контроль качества (Code Quality), матричное тестирование и линтинг.

---

## 🏗️ Бизнес-сценарий (Как это работает)

1.  **Авторизация и Задачи:** Инженер открывает Balance+ IDE и авторизуется через свой GitLab-аккаунт. На главном экране он видит назначенные на него `Issues`.
2.  **Работа с данными:** При выборе задачи приложение "под капотом" работает с Git-репозиторием, где хранятся JSON-файлы с параметрами оборудования (геометрия, режимы).
3.  **Запуск расчёта:** Инженер нажимает "Рассчитать". Оркестратор (`balance-orchestrator`) делегирует сложную математику в фоновый Worker (`condenser-calculator` или `valve-stems`), например, используя метод Бермана.
4.  **Ревью и Утверждение:** После завершения расчета система генерирует графики и визуальные схемы. Инженер нажимает кнопку "Отправить на ревью", и система автоматически создает **Merge Request** в GitLab с кастомным визуальным diff-отчетом (`custom_diff.py`).

---

## 🗺️ Матрица сервисов и портов

Для избежания конфликтов при локальной разработке, за каждым микросервисом жестко закреплены свои порты.

| Микросервис | Компонент | Локальный URL / Порт | Внутренний порт (Docker) |
| :--- | :--- | :--- | :--- |
| **Balance Orchestrator** | Frontend IDE | [http://localhost:3000](http://localhost:3000) | 80 |
| | API Backend | [http://localhost:8005](http://localhost:8005) | 8000 |
| **Condenser Calculator** | API Backend | [http://localhost:8010](http://localhost:8010) | 8000 |
| | PostgreSQL DB | `localhost:5255` | 5432 |
| **Valve Stems** | Frontend | [http://localhost:5252](http://localhost:5252) | - |
| | API Backend | [http://localhost:5253](http://localhost:5253) | 8000 |
| | PostgreSQL DB | `localhost:5254` | 5432 |

---

## 💻 Руководство по локальной разработке

Мы используем смешанный подход: тяжелая инфраструктура крутится в Docker, а код мы запускаем локально через **Poetry** и **npm** для мгновенной перезагрузки (Hot Reload).

### Шаг 1: Инфраструктура (БД и Очереди)
Поднимите базы данных и брокер сообщений в фоновом режиме:
```bash
# В корне проекта
docker-compose up -d db redis 
# (Имена сервисов зависят от вашего docker-compose.yml)
```

### Шаг 2: Бэкенд (FastAPI)
Откройте новую вкладку терминала, перейдите в нужный сервис (например, `valve-stems`) и запустите API:
```bash
cd services/valve-stems/backend
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 5253 --reload
```

### Шаг 3: Фоновые задачи (Celery)
Для работы математического ядра потребуется запустить Worker. Откройте еще одну вкладку терминала:
```bash
cd services/valve-stems/backend
poetry run celery -A app.core.celery_app.celery_app worker --loglevel=info
```

### Шаг 4: Фронтенд (UI)
```bash
cd services/valve-stems/frontend
npm install
npm run dev
# Приложение будет доступно на порту, указанном в vite.config.ts (например, 5252)
```

---

## ⚠️ Важно: Управление Базами Данных (PostgreSQL)

В отличие от классических проектов, на данном этапе мы **НЕ используем автоматическое применение миграций** при старте. 

Структура БД содержит сложную предметную область и эталонные справочники материалов (см. папку `db/materials/`). База разворачивается из SQL-дампа (например, `init.dump` или файлов в папке `_archive/database/sql/`).

**Команда `alembic upgrade head` закомментирована в `entrypoint.sh`.** Не пытайтесь применять миграции на пустую базу! Если вам нужно обновить структуру — используйте скрипт восстановления БД или DBeaver/DataGrip для подключения на порты `5254` / `5255`.

---

## 🧪 Качество кода (QA) и CI

Проект содержит развитую матрицу тестирования, которая запускается через GitHub Actions и скрипт `test_runner.py`.

*   **Модульные и Интеграционные тесты:** Запускаются через `pytest`. Часть бизнес-флоу тестируется с помощью **Tavern** (`.tavern.yaml`).
*   **Линтинг:** Мы используем **Ruff** (см. конфигурацию в `ruff.toml`).
*   **AI Code Review:** Настроен эксклюзивный процесс проверки кода и генерации тестов с помощью нейросетей (см. `.github/workflows/ai-review.yml`).

**Локальный запуск тестов:**
```bash
# Запуск всех тестов проекта
python test_runner.py

# Линтинг
ruff check .
```

---

## 📂 Архитектура и Документация

Полная документация по методам расчетов, форматам JSON, требованиям к оборудованию и ADR (Architecture Decision Records) находится в директории [`/docs`](/docs). 

> **[Смотреть полное дерево проекта (PROJECT_TREE.md) 🌳](PROJECT_TREE.md)**

---

## 🤝 Правила контрибьютинга

1. Код разрабатывается в ветках (Feature Branches).
2. Обязательное прохождение всех тестов и линтеров до создания Merge Request.
3. Обязательное покрытие новых математических стратегий эталонными данными (см. `validation_data/`).
Подробнее в [CONTRIBUTING.md](CONTRIBUTING.md).
