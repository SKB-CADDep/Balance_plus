"""
Репозиторий доступа к данным турбин (Turbines).

Реализует операции поиска, фильтрации и извлечения информации о турбинах 
и связанных с ними клапанах (valves) из базы данных PostgreSQL.
"""

import logging

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import EntityNotFoundError
from app.models import Turbine, Valve
from app.schemas import TurbineValves, ValveInfo

logger = logging.getLogger(__name__)


def search_turbines(
    db: Session,
    query: str | None = None,
    station: str | None = None,
    factory_num: str | None = None,
    valve_drawing: str | None = None,
) -> list[Turbine]:
    """
    Выполняет комплексный поиск турбин по нескольким критериям.
    Поддерживает фильтрацию по имени, станции, заводскому номеру
    и даже по чертежам связанных клапанов.
    Использует Eager Loading (joinedload) для предотвращения N+1 запросов.
    """
    try:
        # WARNING (Технический долг):
        # Аналогично другим CRUD методам, db.query() является устаревшим
        # синтаксисом (legacy) в SQLAlchemy 2.0.
        sql_query = db.query(Turbine).options(joinedload(Turbine.valves))
        filters = []

        if query:
            filters.append(Turbine.name.ilike(f"%{query}%"))
        if station:
            filters.append(Turbine.station_name.ilike(f"%{station}%"))
        if factory_num:
            filters.append(Turbine.factory_number.ilike(f"%{factory_num}%"))
        if valve_drawing:
            # Неявный JOIN для фильтрации по дочерней таблице
            sql_query = sql_query.join(Turbine.valves).filter(
                Valve.name.ilike(f"%{valve_drawing}%")
            )

        if filters:
            sql_query = sql_query.filter(and_(*filters))

        return sql_query.all()
    except Exception as e:
        logger.error(
            "Ошибка поиска турбин",
            extra={"error": str(e)},
            exc_info=True
        )
        return []


def get_turbine_by_id(db: Session, turbine_id: int) -> Turbine:
    """Получает конкретную турбину по её внутреннему ID."""
    turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
    if not turbine:
        raise EntityNotFoundError(entity_name="Турбина", entity_id=turbine_id)
    return turbine


def get_valves_by_turbine_id(db: Session, turbine_id: int) -> TurbineValves:
    """
    Извлекает список всех клапанов (штоков), привязанных к конкретной турбине по её ID.
    Формирует DTO-ответ с подсчетом количества элементов.
    """
    turbine = db.query(Turbine).filter(Turbine.id == turbine_id).first()
    if not turbine:
        raise EntityNotFoundError(entity_name="Турбина", entity_id=turbine_id)

    # WARNING (Архитектурный нюанс):
    # Обращение к turbine.valves может вызвать дополнительный запрос в БД (Lazy Load),
    # если eager-loading не был настроен на уровне самой модели Turbine.
    valves = turbine.valves
    valve_info_list = [ValveInfo.model_validate(v) for v in valves]

    return TurbineValves(count=len(valve_info_list), valves=valve_info_list)


def get_valves_by_turbine(db: Session, turbine_name: str) -> TurbineValves:
    """
    Извлекает список всех клапанов (штоков), привязанных к турбине,
    используя её строковое наименование (name) вместо ID.
    """
    turbine = db.query(Turbine).filter(Turbine.name == turbine_name).first()
    if not turbine:
        raise EntityNotFoundError(
            entity_name="Турбина по имени", entity_id=turbine_name
        )

    valves = turbine.valves
    valve_info_list = [ValveInfo.model_validate(v) for v in valves]

    return TurbineValves(count=len(valve_info_list), valves=valve_info_list)
    