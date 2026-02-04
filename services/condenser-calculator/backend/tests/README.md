```markdown
# Тестирование Condenser Calculator

## Обзор

Тесты сервиса разделены на две категории:

| Тип | Назначение | Скорость | Зависимости |
|-----|------------|----------|-------------|
| **Unit** | Проверка отдельных функций и классов | Быстрые | Минимальные |
| **Validation** | Сравнение с эталонными данными | Медленнее | JSON-файлы |

## Структура тестов

```
tests/
├── conftest.py                 # Общие фикстуры сервиса
│
├── unit/                       # Юнит-тесты
│   ├── test_berman_strategy.py
│   ├── test_metrovickers_strategy.py
│   ├── test_VKU_strategy.py
│   ├── test_division_range.py
│   ├── test_table_models.py
│   ├── test_uniconv.py
│   └── ...
│
└── validation/                 # Валидационные тесты
    ├── README.md
    └── berman/
        ├── conftest.py
        ├── test_verification.py
        ├── test_mode_1.py
        ├── test_mode_2.py
        ├── test_mode_3.py
        └── test_mode_4.py
```

## Быстрый старт

### 1. Перейти в директорию сервиса

```powershell
cd services/condenser-calculator/backend
```

### 2. Установить зависимости

```powershell
poetry install
```

### 3. Запустить все тесты

```powershell
poetry run pytest tests/ -v
```

---

## Юнит-тесты

### Запуск всех юнит-тестов

```powershell
poetry run pytest tests/unit/ -v
```

### Запуск тестов конкретного модуля

```powershell
# Стратегия Бермана
poetry run pytest tests/unit/test_berman_strategy.py -v

# Стратегия Метро-Виккерс
poetry run pytest tests/unit/test_metrovickers_strategy.py -v

# Стратегия ВКУ
poetry run pytest tests/unit/test_VKU_strategy.py -v

# Модуль разбиения диапазонов
poetry run pytest tests/unit/test_division_range.py -v

# Табличные модели
poetry run pytest tests/unit/test_table_models.py -v

# Конвертер единиц
poetry run pytest tests/unit/test_uniconv.py -v
```

### Описание юнит-тестов

| Файл | Тестируемый модуль | Описание |
|------|-------------------|----------|
| `test_berman_strategy.py` | `berman_strategy.py` | Расчёт по методике Бермана |
| `test_metrovickers_strategy.py` | `metrovickers_strategy.py` | Расчёт по методике Метро-Виккерс |
| `test_VKU_strategy.py` | `VKU_strategy.py` | Расчёт ВКУ |
| `test_division_range.py` | `division_range.py` | Разбиение диапазонов значений |
| `test_table_models.py` | `table_models.py` | Модели таблиц данных |
| `test_uniconv.py` | `uniconv.py` | Конвертация единиц измерения |

---

## Валидационные тесты

### Запуск всех валидационных тестов

```powershell
poetry run pytest tests/validation/ -v
```

### Тесты методики Бермана

```powershell
# Все тесты Бермана
poetry run pytest tests/validation/berman/ -v

# Контрольные примеры из документации
poetry run pytest tests/validation/berman/test_verification.py -v

# Конкретный режим
poetry run pytest tests/validation/berman/test_mode_1.py -v
poetry run pytest tests/validation/berman/test_mode_2.py -v
poetry run pytest tests/validation/berman/test_mode_3.py -v
poetry run pytest tests/validation/berman/test_mode_4.py -v
```

### Описание режимов

| Режим | Файл | Конфигурация | Особенности |
|-------|------|--------------|-------------|
| Mode 1 | `test_mode_1.py` | ОП + ВП | t1_main = t1_builtin |
| Mode 2 | `test_mode_2.py` | ОП + ВП | t1_builtin = t1_main + 3°C |
| Mode 3 | `test_mode_3.py` | Только ОП | W_builtin = 0 |
| Mode 4 | `test_mode_4.py` | Только ОП | Расширенный диапазон, G_air = 20 |

---

## Команды запуска

### Основные команды

```powershell
# Все тесты
poetry run pytest tests/ -v

# Только юнит-тесты
poetry run pytest tests/unit/ -v

# Только валидационные тесты
poetry run pytest tests/validation/ -v

# Быстрая проверка (без подробного вывода)
poetry run pytest tests/
```

### Фильтрация тестов

```powershell
# По имени теста
poetry run pytest tests/ -v -k "test_pressure"

# По маркеру
poetry run pytest tests/ -v -m "slow"
poetry run pytest tests/ -v -m "validation"

# Исключить медленные тесты
poetry run pytest tests/ -v -m "not slow"
```

### Отладка

```powershell
# Остановиться на первой ошибке
poetry run pytest tests/ -v -x

# Подробный вывод ошибок
poetry run pytest tests/ -v --tb=long

# Показать print() в тестах
poetry run pytest tests/ -v -s

# Только упавшие в прошлый раз
poetry run pytest tests/ -v --lf

# Сначала упавшие
poetry run pytest tests/ -v --ff
```

### Отчёты

```powershell
# Показать 10 самых медленных тестов
poetry run pytest tests/ -v --durations=10

# Покрытие кода
poetry run pytest tests/ --cov=app/utils --cov-report=html

# Покрытие в терминале
poetry run pytest tests/ --cov=app/utils --cov-report=term-missing
```

---

## Эталонные данные

Расположены в корне монорепозитория:

```
validation_data/
└── condenser-calculator/
    └── strategies/
        └── berman/
            ├── geometrys/
            │   ├── geometry.json       # Стандартная геометрия
            │   └── geometry_4.json     # Геометрия для mode_4
            ├── modes/
            │   ├── mode_1.json         # Параметры режима 1
            │   ├── mode_2.json         # Параметры режима 2
            │   ├── mode_3.json         # Параметры режима 3
            │   └── mode_4.json         # Параметры режима 4
            └── results/
                ├── results_1.json      # Эталонные результаты режима 1
                ├── results_2.json      # Эталонные результаты режима 2
                ├── results_3.json      # Эталонные результаты режима 3
                └── results_4.json      # Эталонные результаты режима 4
```

---

## Контрольные примеры

Из раздела 8 документации `CALC-COND-BERMAN.md`:

### Температура насыщения (раздел 8.1)

| Сценарий | W_main | W_builtin | Ожидаемое t_sat |
|----------|--------|-----------|-----------------|
| Только ОП | 12000 | 0 | 30.898°C |
| ОП + ВП | 12000 | 4000 | 28.173°C |
| Только ВП | 0 | 4000 | 52.694°C |

**Условия**: G_steam = 200 т/ч, t1 = 20°C, β = 1.0

### Давление эжекторов (раздел 8.2)

| Кол-во эжекторов | Ожидаемое давление |
|------------------|-------------------|
| 1 | 0.03955 кгс/см² |
| 2 | 0.03702 кгс/см² |

**Условия**: t1 = 20°C, G_air = 16.5 кг/ч

---

## Маркеры тестов

Определены в `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "validation: marks validation tests",
]
```

### Использование маркеров

```python
# В тестовом файле
import pytest

@pytest.mark.slow
def test_heavy_calculation():
    ...

@pytest.mark.validation
def test_against_reference_data():
    ...
```

### Запуск по маркерам

```powershell
# Только медленные
poetry run pytest tests/ -v -m "slow"

# Всё кроме медленных
poetry run pytest tests/ -v -m "not slow"

# Только валидационные
poetry run pytest tests/ -v -m "validation"
```

---

## Добавление новых тестов

### Юнит-тест

```python
# tests/unit/test_new_module.py

import pytest
from app.utils.new_module import NewClass


class TestNewClass:
    """Тесты для NewClass."""
    
    def test_initialization(self):
        """Проверка создания экземпляра."""
        obj = NewClass()
        assert obj is not None
    
    def test_calculation(self):
        """Проверка расчёта."""
        obj = NewClass()
        result = obj.calculate(input_value=10)
        assert result == expected_value
    
    @pytest.mark.parametrize("input_val, expected", [
        (1, 10),
        (2, 20),
        (3, 30),
    ])
    def test_parametrized(self, input_val, expected):
        """Параметризованный тест."""
        obj = NewClass()
        assert obj.calculate(input_val) == expected
```

### Валидационный тест

См. раздел "Добавление новых тестов" в документации по валидации.

---

## Устранение проблем

### ModuleNotFoundError

```powershell
# Проверить что pythonpath настроен
poetry run python -c "import sys; print(sys.path)"

# Проверить импорт
poetry run python -c "from app.utils.berman_strategy import BermanStrategy; print('OK')"
```

В `pyproject.toml` должно быть:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

### Тесты не находятся

```powershell
# Проверить что pytest видит тесты
poetry run pytest tests/ --collect-only

# Проверить конкретную директорию
poetry run pytest tests/unit/ --collect-only
poetry run pytest tests/validation/ --collect-only
```

### Ошибки импорта в тестах

```powershell
# Проверить синтаксис файла
poetry run python -m py_compile tests/unit/test_berman_strategy.py
```

---

## CI/CD интеграция

```yaml
# .github/workflows/test-condenser.yml
name: Condenser Calculator Tests

on:
  push:
    paths:
      - 'services/condenser-calculator/**'
      - 'validation_data/condenser-calculator/**'
  pull_request:
    paths:
      - 'services/condenser-calculator/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/condenser-calculator/backend
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run unit tests
        run: poetry run pytest tests/unit/ -v --tb=short

  validation-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/condenser-calculator/backend
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Poetry
        run: pip install poetry
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run validation tests
        run: poetry run pytest tests/validation/ -v --tb=short
```

---

## Связанные документы

- [CALC-COND-BERMAN.md](../../../../../docs/methods/balance/CALC-COND-BERMAN.md) — методика Бермана
- [CALC-COND-METRO_VIKKERS.md](../../../../../docs/methods/balance/CALC-COND-METRO_VIKKERS.md) — методика Метро-Виккерс
- [DB-EQUIP-CONDENSER.md](../../../../../docs/methods/database_structure/DB-EQUIP-CONDENSER.md) — структура БД
```

---

## Краткая шпаргалка

Также можно создать короткий файл `services/condenser-calculator/backend/tests/README.md`:

```markdown
# Тесты Condenser Calculator

## Быстрый старт

```powershell
cd services/condenser-calculator/backend
poetry install
poetry run pytest tests/ -v
```

## Команды

| Команда | Описание |
|---------|----------|
| `poetry run pytest tests/ -v` | Все тесты |
| `poetry run pytest tests/unit/ -v` | Юнит-тесты |
| `poetry run pytest tests/validation/ -v` | Валидационные тесты |
| `poetry run pytest tests/ -v -x` | Остановиться на первой ошибке |
| `poetry run pytest tests/ -v --tb=long` | Подробный вывод ошибок |
| `poetry run pytest tests/ -v -k "berman"` | Тесты содержащие "berman" |

## Структура

```
tests/
├── unit/                    # Быстрые тесты отдельных модулей
└── validation/              # Сравнение с эталонными данными
    └── berman/              # Методика Бермана
```

Подробнее: [tests/validation/README.md](validation/README.md)