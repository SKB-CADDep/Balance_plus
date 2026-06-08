"""
API-маршрутизатор для работы со справочником конденсаторов.

Предоставляет эндпоинты для получения списка доступных конденсаторов,
поиска по каталогу и извлечения детальной геометрии/характеристик 
конкретного аппарата для последующих расчетов.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud.condensers import get_condenser_by_id, get_condensers, search_condensers
from app.dependencies import get_db
from app.schemas.condenser import CondenserDetail, CondenserShort

router = APIRouter(tags=["Condensers"])


@router.get(
    "/condensers",
    response_model=list[CondenserShort],
    summary="Список конденсаторов",
)
async def list_condensers(
    search: str | None = Query(None, description="Поиск по названию или проекту"),
    db: Session = Depends(get_db),
):
    """
    Возвращает список доступных конденсаторов в кратком формате.

    Поддерживает опциональную фильтрацию (поиск). Модель ответа (CondenserShort) 
    специально облегчена и не содержит тяжелых геометрических массивов, 
    чтобы не перегружать сеть при отрисовке таблиц или селекторов на фронтенде.

    Args:
        search (str | None): Строка для текстового поиска по названию аппарата 
            или имени проекта. Если None, возвращается весь каталог.
        db (Session): Сессия базы данных (Dependency Injection).

    Returns:
        list[CondenserShort]: Список базовых моделей конденсаторов.
    """
    if search:
        # Делегирование логики поиска (LIKE/ILIKE) на уровень базы данных
        return search_condensers(db, search)
    return get_condensers(db)


@router.get(
    "/condensers/{condenser_id}",
    response_model=CondenserDetail,
    summary="Получить конденсатор по ID",
)
async def get_condenser(condenser_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о конденсаторе по его идентификатору.

    Используется для загрузки полной карточки аппарата, включая все 
    геометрические параметры, необходимые для выполнения расчетов 
    (Бермана, Метро-Виккерса) или визуализации чертежей.

    Args:
        condenser_id (int): Уникальный идентификатор конденсатора в БД.
        db (Session): Сессия базы данных (Dependency Injection).

    Returns:
        CondenserDetail: Полная Pydantic-модель конденсатора со вложенными структурами.

    Raises:
        HTTPException / EntityNotFoundError: Если аппарат не найден 
            (ошибка генерируется на уровне CRUD-слоя и должна перехватываться 
            глобальным обработчиком исключений FastAPI).
    """
    return get_condenser_by_id(db, condenser_id)