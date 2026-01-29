"""
Конфигурационный файл pytest для настройки путей импорта модулей.

Добавляет пути к микросервисам в sys.path, чтобы тесты могли импортировать
модули app и utils без ошибок.
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
