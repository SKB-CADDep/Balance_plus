import gitlab.exceptions
from fastapi import APIRouter, HTTPException

from app.core.gitlab_adapter import gitlab_client


router = APIRouter(prefix="/user", tags=["User"])

@router.get("/me")
async def get_current_user():
    try:
        # Убеждаемся, что соединение есть
        gitlab_client.check_connection()
        user = gitlab_client.gl.user
        return {
            "name": user.name,          # Константинопольский К.
            "username": user.username,  # k.konstantinopolsky
            "avatar_url": user.avatar_url
        }
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception:
        return {"name": "Гость", "username": "guest", "avatar_url": ""}
