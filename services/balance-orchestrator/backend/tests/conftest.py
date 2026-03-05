"""
Локальный conftest для тестов balance-orchestrator backend.

Делает `app.*` импортируемым при запуске `pytest` из директории сервиса.
"""

from __future__ import annotations

import sys
from pathlib import Path

import os
import pytest
import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
import importlib.util
import datetime
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]  # .../backend
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# --- 1. PYDANTIC МОДЕЛИ ДЛЯ ВАЛИДАЦИИ YAML ---
class DBTestStep(BaseModel):
    id: str
    description: Optional[str] = "Без описания"
    query: str
    params: Optional[Dict[str, Any]] = None
    expected_count: Optional[int] = None
    expected_rows: Optional[List[Dict[str, Any]]] = None

class DBTestSuite(BaseModel):
    description: str
    tests: List[DBTestStep]

# --- 2. ИСПОЛНИТЕЛЬ КОНКРЕТНОГО ТЕСТА ---
class DBYamlItem(pytest.Item):
    def __init__(self, name, parent, spec: DBTestStep):
        super().__init__(name, parent)
        self.spec = spec

    def runtest(self):
        # Берем URL базы из переменных окружения (по умолчанию - тестовая БД)
        db_url = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db")
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
                    assert result.rowcount == self.spec.expected_count, \
                        f"Ожидалось затронуть {self.spec.expected_count} строк, по факту: {result.rowcount}"
                
                # 2. Проверяем возвращенные данные (SELECT или RETURNING)
                if self.spec.expected_rows is not None:
                    rows = [dict(row._mapping) for row in result]
                    
                    assert len(rows) == len(self.spec.expected_rows), \
                        f"Ожидалось {len(self.spec.expected_rows)} записей, получено {len(rows)}"
                    
                    for expected_row, actual_row in zip(self.spec.expected_rows, rows):
                        for key, expected_val in expected_row.items():
                            assert key in actual_row, f"Колонка '{key}' отсутствует в результате"
                            assert actual_row[key] == expected_val, \
                                f"Колонка '{key}': ожидалось {expected_val}, получено {actual_row[key]}"
            finally:
                # ОЧЕНЬ ВАЖНО: Откатываем изменения, чтобы база осталась чистой
                trans.rollback() 

    def reportinfo(self):
        return self.path, 0, f"DB Test: {self.name} ({self.spec.description})"

# --- 3. СБОРЩИК ФАЙЛОВ .db.yaml ---
class DBYamlFile(pytest.File):
    def collect(self):
        # Читаем YAML
        raw_data = yaml.safe_load(self.path.open(encoding="utf-8"))
        
        # Валидируем через Pydantic (выдаст красивую ошибку, если YAML кривой)
        # Для Pydantic v2: model_validate. Для v1: parse_obj
        suite = DBTestSuite.model_validate(raw_data) if hasattr(DBTestSuite, 'model_validate') else DBTestSuite.parse_obj(raw_data)
        
        # Генерируем тесты
        for test_spec in suite.tests:
            yield DBYamlItem.from_parent(self, name=test_spec.id, spec=test_spec)

# --- ПЛАГИН ДЛЯ ТЕСТИРОВАНИЯ МАТЕМАТИКИ И СТРАТЕГИЙ (*.calc.py) ---
class CalcItem(pytest.Item):
    def __init__(self, name, parent, spec, target_func):
        super().__init__(name, parent)
        self.spec = spec
        self.target_func = target_func

    def runtest(self):
        # Достаем входные данные и ожидаемый результат
        input_data = self.spec.get("input", {})
        expected = self.spec.get("expected")
        
        # Вызываем реальную стратегию расчета
        result = self.target_func(**input_data)
        
        # Умная сверка (поддерживает как словари, так и простые числа)
        if isinstance(expected, dict) and isinstance(result, dict):
            for key, val in expected.items():
                actual_val = result.get(key)
                assert actual_val == val, f"Ключ '{key}': ожидалось {val}, получено {actual_val}"
        else:
            assert result == expected, f"Ожидалось {expected}, получено {result}"

    def reportinfo(self):
        return self.path, 0, f"Math Test: {self.name}"

class CalcFile(pytest.File):
    def collect(self):
        # Динамически импортируем python-файл как модуль
        spec = importlib.util.spec_from_file_location("calc_module", self.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Ищем целевую функцию и массив с тестами
        target_func = getattr(module, "target_function", None)
        tests = getattr(module, "tests",[])
        
        if not target_func:
            raise ValueError(f"В файле {self.path.name} не указана переменная 'target_function'!")
            
        for i, test_spec in enumerate(tests):
            test_name = test_spec.get("id", f"calc_test_{i}")
            yield CalcItem.from_parent(self, name=test_name, spec=test_spec, target_func=target_func)

def pytest_collect_file(file_path: Path, parent):
    # Перехват DB-файлов
    if file_path.name.endswith(".db.yaml"):
        return DBYamlFile.from_parent(parent, path=file_path)
    # Перехват файлов с математикой (ЗАМЕНИЛИ .calc.py НА _calc.py)
    elif file_path.name.endswith("_calc.py"):
        return CalcFile.from_parent(parent, path=file_path)
    
# --- АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ ЛОГОВ ПРИ ОШИБКАХ ---
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # 🔥 НОВОЕ: Проверяем, включил ли пользователь логи в Оркестраторе
    if os.getenv("SAVE_TEST_LOGS") != "1":
        return  # Если не включено, просто выходим и ничего не сохраняем

    # Если тест упал именно во время выполнения (call)
    if report.when == "call" and report.failed:
        file_path = Path(item.location[0])
        base_name = file_path.name.split('.')[0]
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        log_filename = f"log_{base_name}_{now_str}.txt"
        
        with open(log_dir / log_filename, "w", encoding="utf-8") as f:
            f.write(f"УПАВШИЙ ТЕСТ: {item.nodeid}\n")
            f.write("="*60 + "\n")
            f.write(report.longreprtext)