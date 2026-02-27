import logging
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class UnitsDictionaryResponse(BaseModel):
    parameters: dict[str, list[str]]


@router.get("/units", response_model=UnitsDictionaryResponse, summary="Получить справочник единиц измерения")
async def get_available_units():
    """
    Возвращает доступные физические параметры и их единицы измерения.
    Фронтенд использует этот эндпоинт для рендера выпадающих списков (Select).
    """
    # TODO: Заменить хардкод на реальный вызов экземпляра converter.
    # Например: units_data = converter.get_all_units_dict()

    units_data = {
        "pressure": ["кгс/см²", "МПа", "Па", "кПа", "бар", "атм (тех)", "атм (физ)"],
        "temperature": ["°C", "K", "°F"],
        "enthalpy": ["ккал/кг", "кДж/кг"],
        "mass_flow": ["т/ч", "кг/с"],
    }

    return UnitsDictionaryResponse(parameters=units_data)
