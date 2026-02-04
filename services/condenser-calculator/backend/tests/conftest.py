"""
Общие фикстуры для тестов сервиса condenser-calculator.

Важно: тесты должны запускаться автономно из директории сервиса:
`services/condenser-calculator/backend`.
"""

from __future__ import annotations

import sys
from pathlib import Path


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


def pytest_configure(config):
    # Удобно видеть корень данных в отчёте (и отлаживать пути)
    config._condenser_validation_data_path = str(VALIDATION_DATA_PATH)


