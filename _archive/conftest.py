"""
АРХИВ: старый корневой conftest.py.

Ранее добавлял пути к бэкендам сервисов в sys.path для запуска тестов из корня.
После миграции тестов внутрь сервисов больше не нужен.
"""

import sys
import os

# Получаем абсолютный путь к корню проекта
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Добавляем пути к микросервисам
BALANCE_ORCHESTRATOR_BACKEND = os.path.join(PROJECT_ROOT, "services", "balance-orchestrator", "backend")
CONDENSER_CALCULATOR_BACKEND = os.path.join(PROJECT_ROOT, "services", "condenser-calculator", "backend")

# Добавляем пути в sys.path, если их там еще нет
if BALANCE_ORCHESTRATOR_BACKEND not in sys.path:
    sys.path.insert(0, BALANCE_ORCHESTRATOR_BACKEND)

if CONDENSER_CALCULATOR_BACKEND not in sys.path:
    sys.path.insert(0, CONDENSER_CALCULATOR_BACKEND)

