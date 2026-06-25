"""
Инициализационный модуль пакета работы с БД (Слой CRUD).

Этот файл работает как архитектурный фасад (Facade) для всего CRUD-слоя.
Он агрегирует функции из отдельных подмодулей (condensers, materials, calculations) 
и экспортирует их наверх. Это позволяет другим слоям приложения (например, роутерам) 
импортировать функции напрямую из `app.crud`, делая код более чистым и читаемым, 
избегая глубоких путей импорта.
"""

from .condensers import get_condenser_by_id, get_condensers, search_condensers
from .materials import get_materials, get_material_by_id, get_material_by_uuid
from .calculations import save_calculation_result

# Явное указание публичного API этого пакета.
# Защищает от случайного импорта внутренних переменных или модулей 
# при использовании конструкции `from app.crud import *`.
__all__ = [
        "get_condenser_by_id",
        "get_condensers",
        "search_condensers",
        "get_materials",
        "get_material_by_id",
        "get_material_by_uuid",
        "save_calculation_result",
]