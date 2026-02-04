"""
Общая настройка путей для скриптов.
Импортировать в начале каждого скрипта:

    from _common import setup_path
    setup_path()
"""

import sys
from pathlib import Path


def setup_path():
    """Добавляет путь к app в PYTHONPATH."""
    backend_path = Path(__file__).parent.parent
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
