import logging
from fastapi import APIRouter
from app.core.converter import converter


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/units", summary="Получить справочник единиц измерения")
def get_units_dictionary() -> dict:
    result = {}
    for param_type, param_data in converter.parameters.items():
        result[param_type] = {
            "name": param_data["name"],          
            "base": param_data["base"],          
            "available": list(param_data["units"].keys())  
        }
    return result
