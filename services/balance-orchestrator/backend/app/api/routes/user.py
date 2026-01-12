from fastapi import APIRouter
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
    except Exception:
        return {"name": "Гость", "username": "guest", "avatar_url": ""}