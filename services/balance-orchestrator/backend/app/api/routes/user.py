import gitlab.exceptions
from fastapi import APIRouter, HTTPException

from app.core.gitlab_adapter import GitLabConfigurationError, gitlab_client


router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me")
async def get_current_user():
    try:
        user = gitlab_client.get_current_user()
        return {
            "name": user.name,  # Константинопольский К.
            "username": user.username,  # k.konstantinopolsky
            "avatar_url": user.avatar_url,
        }
    except GitLabConfigurationError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения пользователя: {type(e).__name__}")
