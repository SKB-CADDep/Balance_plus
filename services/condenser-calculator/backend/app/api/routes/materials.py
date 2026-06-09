"""
API-маршрутизатор для работы со справочником материалов.

Предоставляет эндпоинты для получения списка трубных материалов (сплавов, металлов),
используемых в конденсаторах. Свойства материала (например, коэффициент теплопроводности) 
критически важны для работы физического ядра при расчете коэффициента теплопередачи.
"""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.crud.materials import (
    get_materials, 
    get_materials_by_condenser
)
from app.dependencies import get_db
from app.schemas.material import MaterialShort

router = APIRouter(tags=["Materials"])


@router.get(
    "/materials",
    response_model=list[MaterialShort],
    summary="Список всех материалов в базе",
)
def list_materials(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Возвращает полный список доступных материалов с поддержкой пагинации.

    Используется для формирования общих справочников или селекторов на фронтенде
    без привязки к конкретному оборудования.

    Args:
        skip (int): Смещение для пагинации (количество пропускаемых записей). По умолчанию 0.
        limit (int): Максимальное количество возвращаемых записей. По умолчанию 100.
        db (Session): Сессия базы данных (Dependency Injection).

    Returns:
        list[MaterialShort]: Краткий список моделей материалов (ID, название и т.п.).
    """
    return get_materials(db, skip=skip, limit=limit)


@router.get(
    "/condensers/{condenser_id}/materials",
    response_model=list[MaterialShort],
    summary="Список материалов для конкретного конденсатора",
)
def list_condenser_materials(
    condenser_id: int = Path(..., description="ID конденсатора"), 
    db: Session = Depends(get_db)
):
    """
    Возвращает материалы, из которых могут быть изготовлены трубки выбранного конденсатора.

    Бизнес-логика: Разные модели конденсаторов исторически (по чертежам, ГОСТ/ТУ) 
    проектировались под определенные сплавы (например, латунь, мельхиор, титан, нержавеющая сталь). 
    Этот эндпоинт позволяет фронтенду отфильтровать селектор так, чтобы 
    пользователь не выбрал физически невозможный вариант для расчета (защита от "дурака").

    Args:
        condenser_id (int): Уникальный идентификатор конденсатора (передается в пути запроса).
        db (Session): Сессия базы данных (Dependency Injection).

    Returns:
        list[MaterialShort]: Список допустимых материалов для конкретного аппарата.
    """
    return get_materials_by_condenser(db, condenser_id)