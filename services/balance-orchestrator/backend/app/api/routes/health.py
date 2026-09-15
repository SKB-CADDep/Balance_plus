import gitlab.exceptions
from fastapi import APIRouter, HTTPException, status

from app.core.gitlab_adapter import (
    GitLabConfigurationError,
    gitlab_client,
)


router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Быстрая проверка API без сетевого обращения к GitLab."""
    summary = gitlab_client.connection_summary()
    return {
        "status": "ok",
        "service": "balance-orchestrator",
        "gitlab": summary,
    }


@router.get("/health/gitlab")
async def gitlab_health_check():
    """Проверяет legacy token или сообщает готовность user-OAuth configuration."""
    summary = gitlab_client.connection_summary()
    if summary.get("auth_mode") == "oauth":
        return {
            "status": "ok",
            "check": "per-user GitLab authorization is validated on protected requests",
            "gitlab": summary,
        }

    try:
        return gitlab_client.check_connection(check_project=True)
    except GitLabConfigurationError as exc:
        error_type = "configuration"
        message = str(exc)
    except gitlab.exceptions.GitlabAuthenticationError:
        error_type = "authentication"
        message = "GitLab отклонил токен. Создайте новый токен со scope api."
    except gitlab.exceptions.GitlabError as exc:
        error_type = type(exc).__name__
        message = "GitLab недоступен или вернул ошибку API."
    except Exception as exc:
        error_type = type(exc).__name__
        message = "Не удалось подключиться к GitLab. Проверьте DNS, URL и сеть."

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "status": "error",
            "error_type": error_type,
            "message": message,
            "gitlab": gitlab_client.connection_summary(),
        },
    )
