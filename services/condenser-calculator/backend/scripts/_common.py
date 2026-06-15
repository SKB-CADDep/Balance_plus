"""
Утилита для настройки системных путей (Python Path).

Этот модуль импортируется в начале каждого standalone-скрипта 
(находящегося в директории `scripts/`), чтобы обеспечить 
корректный импорт модулей из основной директории приложения `app/`.

Пример использования:
    from _common import setup_path
    setup_path()
"""

import sys
from pathlib import Path


def setup_path() -> None:
    """
    Добавляет корневую директорию бэкенда в начало `PYTHONPATH`.

    [ENGINEERING CONTEXT]
    Почему это сделано так (sys.path hack): 
    Когда скрипт запускается напрямую из терминала (например, `python scripts/my_script.py`), 
    интерпретатор Python добавляет в `sys.path` директорию самого скрипта (`scripts/`), 
    а не корень проекта (`backend/`). Из-за этого импорты абсолютных путей 
    (например, `from app.core import config`) падают с ошибкой ModuleNotFoundError. 
    Вставка `backend_path` под индексом 0 заставляет систему импортов искать 
    модули в корне проекта в первую очередь, решая эту проблему без настройки виртуального окружения.
    """
    backend_path = Path(__file__).parent.parent
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
        