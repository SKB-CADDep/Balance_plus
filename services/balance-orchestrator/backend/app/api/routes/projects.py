# api/routes/projects.py
from fastapi import APIRouter, Query
from app.core.gitlab_adapter import gitlab_client

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("")
async def list_projects(search: str = Query("", description="Поиск по названию проекта")):
    """Список проектов для выбора при создании задачи"""
    return gitlab_client.get_user_projects(search)

