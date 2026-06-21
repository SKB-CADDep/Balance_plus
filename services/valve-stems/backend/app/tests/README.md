# Тесты сервиса valve-stems

---

## Структура директорий

```
app/tests/
├── conftest.py          # sys.path, плагины (*.db.yaml, *_calc.py), сохранение логов
├── README.md            # этот файл
│
├── api/                 # быстрые интеграционные HTTP-тесты (httpx + ASGI)
│   ├── __group__.yml
│   ├── conftest.py      # SQLite in-memory, async_client, override_get_db
│   ├── test_health.py
│   ├── test_turbines.py
│   ├── test_valves.py
│   ├── test_calculation.py
│   └── test_negative_validation.py
│
├── crud/                # тесты слоя app.crud.* (без HTTP)
│   ├── __group__.yml
│   ├── conftest.py      # те же DB-фикстуры, что и в api/
│   └── test_crud.py     # тесты CRUD + хелперы create_test_*
│
├── utils/               # юнит-тесты математики и расчётных модулей
└── scripts/             # smoke-тесты инфраструктуры (pre-start и т.п.)

Balance_plus/tests/e2e/  # E2E — отдельно от сервиса (см. ниже)
```

### За что отвечает каждая группа

| Папка | Что проверяем | Скорость | Нужен живой сервер? |
|-------|---------------|----------|---------------------|
| `api/` | HTTP-эндпоинты, коды ответов, JSON | быстро | нет |
| `crud/` | функции `app.crud.*` напрямую | очень быстро | нет |
| `utils/` | физика, калькуляторы | мгновенно | нет |
| `tests/e2e/` (монорепо) | полный сценарий «как у пользователя» | медленно | **да** (`:5253`) |

### Почему E2E лежит отдельно

E2E-тесты (`tests/e2e/test_full_cycle.tavern.yaml`) — это **Tavern-сценарии** против реального backend на `http://localhost:5253`. Они:

- требуют запущенный сервис и БД с данными;
- проверяют тяжёлый расчёт end-to-end;
- не должны смешиваться с быстрыми API-тестами в `api/`.

API-тесты поднимают приложение **внутри pytest** через `ASGITransport` и **не трогают** production PostgreSQL.

---

## Запуск тестов

### Требования

- **Python 3.12+** (см. `pyproject.toml`: `requires-python = ">=3.12"`)
- venv в `services/valve-stems/backend/.venv`
- для E2E дополнительно: `pip install tavern`

### Через test_runner.py (рекомендуется для меню и групп)

Из корня монорепо, **Python из venv**:

```powershell
cd \Balance_plus
.\services\valve-stems\backend\.venv\Scripts\python.exe test_runner.py
```

В меню выберите группу **«Штоки: API-тесты»** или **«Штоки: База Данных (CRUD)»**.

Опция **`[l]`** — сохранять логи при ошибках в `backend/logs/` (работает через `SAVE_TEST_LOGS=1` в корневом `conftest.py`).

### Напрямую через pytest

Из каталога backend:

```powershell
cd services/valve-stems/backend
.\.venv\Scripts\python.exe -m pytest app/tests/api/ -v
.\.venv\Scripts\python.exe -m pytest app/tests/crud/ -v
.\.venv\Scripts\python.exe -m pytest app/tests/api/test_health.py -v
```

Конфиг pytest: `pyproject.toml` → `[tool.pytest.ini_options]` (`asyncio_mode = "auto"`, `pythonpath = ["."]`).

### E2E (отдельно)

```powershell
# 1. Поднять backend valve-stems на :5253
# 2. Установить Tavern
.\.venv\Scripts\python.exe -m pip install tavern

cd \Balance_plus\tests\e2e
..\..\services\valve-stems\backend\.venv\Scripts\python.exe -m pytest test_full_cycle.tavern.yaml -v
```

---

## In-memory SQLite в API-тестах

Файл: `api/conftest.py`.

### Зачем

Production использует PostgreSQL со схемой `autocalc`. В тестах нужна **изолированная** БД без Docker и без риска для реальных данных.

### Как устроено

1. **`sqlite:///:memory:`** + `StaticPool` — одна in-memory база на сессию pytest.
2. **`ATTACH DATABASE ':memory:' AS autocalc`** — эмуляция PostgreSQL-схемы `autocalc` (SQLite не поддерживает схемы нативно).
3. **`Base.metadata.create_all()`** — таблицы из ORM-моделей.
4. **Транзакция на тест** — `db_session` делает `begin()` → тест → `rollback()`. После каждого теста БД «чистая».
5. **`override_get_db`** — FastAPI вместо production `get_db()` получает тестовую сессию.
6. **`async_client`** — httpx бьёт в приложение через `ASGITransport`, без TCP.

Цепочка:

```
async_client → override_get_db → db_session → engine (SQLite in-memory)
```

---

## Паттерн AAA для API-тестов

**Arrange → Act → Assert** — обязательный порядок.

### Arrange (подготовка)

Данные создаются **хелперами и `db_session`**, а не через другие эндпoinты (если тестируете не цепочку).

Хелперы определены в `crud/test_crud.py`:

```python
from app.tests.crud.test_crud import create_test_turbine, create_test_valve
```

Связь турбина ↔ клапан — many-to-many:

```python
turbine = create_test_turbine(db_session, "T-1")
valve = create_test_valve(db_session, "VD-001")
turbine.valves.append(valve)
db_session.commit()
```

### Act (действие)

Один HTTP-запрос через `async_client`:

```python
response = await async_client.get("/health")
response = await async_client.post("/api/v1/turbines", json={"name": "T-1"})
```

### Assert (проверка)

Минимум: **статус** + **ключевые поля JSON**.

```python
assert response.status_code == 200
assert response.json()["status"] == "ok"
```

### Префиксы URL

| Эндпоинт | URL |
|----------|-----|
| Health | `/health`, `/health/db` (без `/api/v1`) |
| API | `/api/v1/turbines`, `/api/v1/valves/`, … |

### Шаблон теста

```python
import pytest
from app.tests.crud.test_crud import create_test_turbine

@pytest.mark.asyncio
async def test_example(async_client, db_session):
    """Краткое описание для test_runner."""
    # Arrange
    create_test_turbine(db_session, "Example")

    # Act
    response = await async_client.get("/api/v1/turbines/")

    # Assert
    assert response.status_code == 200
```

Первую строку docstring раннер показывает как описание файла/теста в меню.

---

## Связанные файлы

- `Balance_plus/test_runner.py` — меню групп тестов
- `Balance_plus/README_TESTING.md` — общее руководство по раннеру монорепо
- `Balance_plus/tests/e2e/README.md` — E2E между сервисами
