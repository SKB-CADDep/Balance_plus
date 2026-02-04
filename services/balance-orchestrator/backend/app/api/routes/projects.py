# api/routes/projects.py
import gitlab.exceptions
from fastapi import APIRouter, HTTPException, Query

from app.core.gitlab_adapter import gitlab_client


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("")
async def list_projects(search: str = Query("", description="Поиск по названию проекта")):
    """Список проектов для выбора при создании задачи"""
    try:
        return gitlab_client.get_user_projects(search)
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка проектов: {e}")

