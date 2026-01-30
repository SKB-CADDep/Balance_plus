# api/routes/config.py
from fastapi import APIRouter
from app.schemas.task import BUREAU_CONFIG

router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/bureaus")
async def get_bureaus():
    """
    Возвращает конфигурацию бюро и модулей для фронтенда.
    Формат ответа соответствует ожидаемому формату фронтенда.
    """
    bureaus = []
    for bureau_code, bureau_data in BUREAU_CONFIG.items():
        modules = [
            {"id": module_code, "label": module_name}
            for module_code, module_name in bureau_data["modules"].items()
        ]
        bureaus.append({
            "id": bureau_code,
            "label": bureau_data["name"],
            "color": bureau_data["color"],
            "modules": modules
        })
    return bureaus

