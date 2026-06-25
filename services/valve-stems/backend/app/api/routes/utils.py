"""
Вспомогательные маршруты (Utils).

Предоставляет эндпоинты для получения метаинформации о сервисе,
например, справочников единиц измерения для фронтенда.
"""

import logging

from fastapi import APIRouter

from app.core.converter import converter

# Выделяем утилиты в отдельный тег для Swagger UI
router = APIRouter(tags=["Utils"])
logger = logging.getLogger(__name__)


@router.get("/units", summary="Получить справочник единиц измерения")
def get_units_dictionary() -> dict:
    """
    Возвращает список всех доступных физических параметров
    и их единиц измерения из глобального конвертера (uniconv).
    
    Используется фронтендом для динамического построения
    выпадающих списков (селекторов) выбора размерностей.
    """
    result = {}

    for param_type, param_data in converter.parameters.items():
        result[param_type] = {
            "name": param_data["name"],
            "base": param_data["base"],
            "available": list(param_data["units"].keys()),
        }

    return result
    