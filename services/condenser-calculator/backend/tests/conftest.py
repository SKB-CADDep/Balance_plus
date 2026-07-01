"""
Общие фикстуры для тестов сервиса condenser-calculator.

Важно: тесты должны запускаться автономно из директории сервиса:
`services/condenser-calculator/backend`.
"""

from __future__ import annotations

import datetime
import importlib.util
import os
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient, ASGITransport
import yaml
from pydantic import BaseModel
from sqlalchemy import create_engine, text


def _find_monorepo_root(start: Path) -> Path:
    """
    Поднимаемся вверх по дереву, пока не найдём корень монорепозитория.
    Критерий: наличие директорий `services/` и `docs/`.
    """
    start = start.resolve()
    for p in [start, *start.parents]:
        if (p / "services").is_dir() and (p / "docs").is_dir():
            return p
    # Fallback: ожидаем, что conftest лежит в services/<svc>/backend/tests/
    return start.parents[4]


# --- sys.path: делаем `app.*` импортируемым ---
BACKEND_ROOT = Path(__file__).resolve().parents[1]  # .../backend
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# --- пути к данным ---
MONOREPO_ROOT = _find_monorepo_root(Path(__file__))
VALIDATION_DATA_PATH = MONOREPO_ROOT / "validation_data"


def pytest_configure(config: pytest.config) -> None:
    # Удобно видеть корень данных в отчёте (и отлаживать пути)
    config._condenser_validation_data_path = str(VALIDATION_DATA_PATH)


# --- 1. PYDANTIC МОДЕЛИ ДЛЯ ВАЛИДАЦИИ YAML ---
class DBTestStep(BaseModel):
    id: str
    description: str | None = "Без описания"
    query: str
    params: dict[str, Any] | None = None
    expected_count: int | None = None
    expected_rows: list[dict[str, Any]] | None = None


class DBTestSuite(BaseModel):
    description: str
    tests: list[DBTestStep]


# --- 2. ИСПОЛНИТЕЛЬ КОНКРЕТНОГО ТЕСТА ---
class DBYamlItem(pytest.Item):
    def __init__(self, name: str, parent: pytest.Node, spec: DBTestStep) -> None:
        super().__init__(name, parent)
        self.spec = spec

    def runtest(self) -> None:
        # Берем URL базы из переменных окружения (по умолчанию - тестовая БД)
        db_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/test_db",
        )
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Начинаем транзакцию (ROLLBACK в конце, чтобы изолировать тесты!)
            trans = conn.begin()
            try:
                stmt = text(self.spec.query)
                params = self.spec.params or {}
                result = conn.execute(stmt, params)

                # 1. Проверяем количество затронутых строк (INSERT/UPDATE/DELETE)
                if self.spec.expected_count is not None:
                    assert result.rowcount == self.spec.expected_count, (
                        f"Ожидалось затронуть {self.spec.expected_count} строк, по факту: {result.rowcount}"
                    )

                # 2. Проверяем возвращенные данные (SELECT или RETURNING)
                if self.spec.expected_rows is not None:
                    rows = [dict(row._mapping) for row in result]

                    assert len(rows) == len(self.spec.expected_rows), (
                        f"Ожидалось {len(self.spec.expected_rows)} записей, получено {len(rows)}"
                    )

                    for expected_row, actual_row in zip(
                        self.spec.expected_rows, rows, strict=False
                    ):
                        for key, expected_val in expected_row.items():
                            assert key in actual_row, (
                                f"Колонка '{key}' отсутствует в результате"
                            )
                            assert actual_row[key] == expected_val, (
                                f"Колонка '{key}': ожидалось {expected_val}, получено {actual_row[key]}"
                            )
            finally:
                # ОЧЕНЬ ВАЖНО: Откатываем изменения, чтобы база осталась чистой
                trans.rollback()

    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, 0, f"DB Test: {self.name} ({self.spec.description})"


# --- 3. СБОРЩИК ФАЙЛОВ .db.yaml ---
class DBYamlFile(pytest.File):
    def collect(self) -> Iterator[DBYamlItem]:
        # Читаем YAML
        raw_data = yaml.safe_load(self.path.open(encoding="utf-8"))

        # Валидируем через Pydantic (выдаст красивую ошибку, если YAML кривой)
        # Для Pydantic v2: model_validate. Для v1: parse_obj
        suite = (
            DBTestSuite.model_validate(raw_data)
            if hasattr(DBTestSuite, "model_validate")
            else DBTestSuite.parse_obj(raw_data)
        )

        # Генерируем тесты
        for test_spec in suite.tests:
            yield DBYamlItem.from_parent(self, name=test_spec.id, spec=test_spec)


# --- ПЛАГИН ДЛЯ ТЕСТИРОВАНИЯ МАТЕМАТИКИ И СТРАТЕГИЙ (*.calc.py) ---
class CalcItem(pytest.Item):
    def __init__(
        self,
        name: str,
        parent: pytest.Node,
        spec: dict[str, Any],
        target_func: Callable[..., Any],
    ) -> None:
        super().__init__(name, parent)
        self.spec = spec
        self.target_func = target_func

    def runtest(self) -> None:
        input_data = self.spec.get("input", {})
        expected = self.spec.get("expected")

        result = self.target_func(**input_data)

        # РЕКУРСИВНАЯ ФУНКЦИЯ ДЛЯ ГЛУБОКОГО СРАВНЕНИЯ С УЧЕТОМ ПОГРЕШНОСТИ
        def assert_dicts_approx(exp: list, act: list, path: str = "") -> None:
            if isinstance(exp, dict) and isinstance(act, dict):
                for k, v in exp.items():
                    assert k in act, f"Ключ '{path}{k}' отсутствует в результате"
                    assert_dicts_approx(v, act[k], path + f"{k}.")
            elif isinstance(exp, list) and isinstance(act, list):
                assert len(exp) == len(act), (
                    f"Массив '{path}': ожидалась длина {len(exp)}, получено {len(act)}"
                )
                for i, (e_val, a_val) in enumerate(zip(exp, act, strict=False)):
                    assert_dicts_approx(e_val, a_val, path + f"[{i}].")
            elif isinstance(exp, (float, int)) and isinstance(act, (float, int)):
                # Сравниваем числа с погрешностью 1e-5 (0.00001)
                assert act == pytest.approx(exp, rel=1e-5), (
                    f"Значение '{path}': ожидалось {exp}, получено {act}"
                )
            else:
                assert act == exp, f"Значение '{path}': ожидалось {exp}, получено {act}"

        # Запускаем проверку
        assert_dicts_approx(expected, result)

    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, 0, f"Math Test: {self.name}"


class CalcFile(pytest.File):
    def collect(self) -> Iterator[CalcItem]:
        # Динамически импортируем python-файл как модуль
        spec = importlib.util.spec_from_file_location("calc_module", self.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Ищем целевую функцию и массив с тестами
        target_func = getattr(module, "target_function", None)
        tests = getattr(module, "tests", [])

        if not target_func:
            raise ValueError(
                f"В файле {self.path.name} не указана переменная 'target_function'!"
            )

        for i, test_spec in enumerate(tests):
            test_name = test_spec.get("id", f"calc_test_{i}")
            yield CalcItem.from_parent(
                self, name=test_name, spec=test_spec, target_func=target_func
            )


def pytest_collect_file(file_path: Path, parent: pytest.Node) -> pytest.File:
    # Перехват DB-файлов
    if file_path.name.endswith(".db.yaml"):
        return DBYamlFile.from_parent(parent, path=file_path)
    # Перехват файлов с математикой (ЗАМЕНИЛИ .calc.py НА _calc.py)
    elif file_path.name.endswith("_calc.py"):
        return CalcFile.from_parent(parent, path=file_path)


# --- АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ ЛОГОВ ПРИ ОШИБКАХ ---
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> None:
    outcome = yield
    report = outcome.get_result()

    # 🔥 НОВОЕ: Проверяем, включил ли пользователь логи в Оркестраторе
    if os.getenv("SAVE_TEST_LOGS") != "1":
        return  # Если не включено, просто выходим и ничего не сохраняем

    # Если тест упал именно во время выполнения (call)
    if report.when == "call" and report.failed:
        file_path = Path(item.location[0])
        base_name = file_path.name.split(".")[0]
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        log_filename = f"log_{base_name}_{now_str}.txt"

        with open(log_dir / log_filename, "w", encoding="utf-8") as f:
            f.write(f"УПАВШИЙ ТЕСТ: {item.nodeid}\n")
            f.write("=" * 60 + "\n")
            f.write(report.longreprtext)
# --- ASYNC CLIENT FIXTURE ДЛЯ ИНТЕГРАЦИОННЫХ ТЕСТОВ ---
@pytest.fixture
def async_client():
    """Fixture для интеграционных тестов через httpx"""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
