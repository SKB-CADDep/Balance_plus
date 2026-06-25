"""
Инициализатор пакета моделей базы данных (SQLAlchemy ORM).

Этот модуль собирает все классы таблиц из разрозненных файлов в единое пространство имен.
Обеспечивает удобный импорт моделей в других частях приложения (например, `from app.models import Turbine`).
"""

# [ENGINEERING CONTEXT]
# Почему важно импортировать сюда ВСЕ модели SQLAlchemy:
# Инструмент миграций базы данных (Alembic) в файле `env.py` импортирует `Base.metadata`.
# Alembic увидит (и создаст в БД) только те таблицы, классы которых были физически 
# импортированы в память интерпретатора до вызова миграций. 
# Если создать новый файл модели (например, user.py), но забыть добавить его сюда, 
# Alembic "не заметит" новую таблицу и не сгенерирует для неё миграцию.

from app.models.calculation_result import CalculationResultDB
from app.models.turbine import Turbine
from app.models.valve import Valve


# Явное указание публичного интерфейса модуля
__all__ = [
    "CalculationResultDB",
    "Turbine",
    "Valve",
]
