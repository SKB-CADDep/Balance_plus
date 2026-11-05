"""
Локальный conftest для тестов balance-orchestrator backend.

Делает `app.*` импортируемым при запуске `pytest` из директории сервиса.
"""

from __future__ import annotations

import datetime
import importlib.util
import os
import sys
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]  # .../backend
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# --- ПЛАГИН ДЛЯ ТЕСТИРОВАНИЯ МАТЕМАТИКИ И СТРАТЕГИЙ (*.calc.py) ---
class CalcItem(pytest.Item):
    def __init__(self, name, parent, spec, target_func):
        super().__init__(name, parent)
        self.spec = spec
        self.target_func = target_func

    def runtest(self):
        input_data = self.spec.get("input", {})
        expected = self.spec.get("expected")

        result = self.target_func(**input_data)

        # РЕКУРСИВНАЯ ФУНКЦИЯ ДЛЯ ГЛУБОКОГО СРАВНЕНИЯ С УЧЕТОМ ПОГРЕШНОСТИ
        def assert_dicts_approx(exp, act, path=""):
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
        tests = getattr(module, "tests", [])

        if not target_func:
            raise ValueError(f"В файле {self.path.name} не указана переменная 'target_function'!")

        for i, test_spec in enumerate(tests):
            test_name = test_spec.get("id", f"calc_test_{i}")
            yield CalcItem.from_parent(
                self, name=test_name, spec=test_spec, target_func=target_func
            )


def pytest_collect_file(file_path: Path, parent):
    # Перехват файлов с математикой (ЗАМЕНИЛИ .calc.py НА _calc.py)
    if file_path.name.endswith("_calc.py"):
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
        base_name = file_path.name.split(".")[0]
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
        log_filename = f"log_{base_name}_{now_str}.txt"

        with open(log_dir / log_filename, "w", encoding="utf-8") as f:
            f.write(f"УПАВШИЙ ТЕСТ: {item.nodeid}\n")
            f.write("=" * 60 + "\n")
            f.write(report.longreprtext)
