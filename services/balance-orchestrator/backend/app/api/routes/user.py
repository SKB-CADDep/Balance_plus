"""
Роутер для работы с данными текущего пользователя.
Обеспечивает интеграцию профиля пользователя (имя, аватар) из GitLab в интерфейс оркестратора.
"""
import gitlab.exceptions
from fastapi import APIRouter, HTTPException

from app.core.gitlab_adapter import gitlab_client


router = APIRouter(prefix="/user", tags=["User"])


@router.get(
    "/me",
    summary="Получение профиля текущего пользователя",
    response_description="Объект с базовой информацией профиля GitLab (имя, логин, аватар)"
)
async def get_current_user():
    """
    Возвращает информацию о текущем авторизованном пользователе.

    Функция валидирует текущую сессию/токен в GitLab и извлекает метаданные 
    пользователя для отображения в шапке фронтенд-приложения.

    Returns:
        dict: Словарь с данными пользователя:
            - name (str): Отображаемое имя (например, "Константинопольский К.").
            - username (str): Системный логин (например, "k.konstantinopolsky").
            - avatar_url (str): Прямая ссылка на изображение профиля.

    Raises:
        HTTPException (401): Если токен недействителен (ошибка авторизации).
        HTTPException (502): При проблемах доступа к GitLab API.
    """
    try:
        # [ENGINEERING CONTEXT]
        # Принудительная валидация соединения:
        # Объект `gitlab_client.gl.user` в библиотеке python-gitlab использует "lazy loading" 
        # (ленивую загрузку) или может быть закеширован. Прямое обращение к его атрибутам 
        # не всегда гарантирует отправку реального сетевого запроса к GitLab.
        # Вызов `check_connection()` принудительно пингует сервер, гарантируя, 
        # что токен до сих пор валиден, и мы не отдадим устаревшие данные профиля.
        
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
        # [ENGINEERING CONTEXT]
        # Стратегия Graceful Degradation (Изящная деградация):
        # Если возникает непредвиденная ошибка парсинга или локальный сбой, 
        # мы намеренно подавляем ошибку 500 и возвращаем заглушку "Гость".
        # Это защищает фронтенд-приложение от падения (White screen of death) 
        # из-за невозможности отрендерить аватарку в шапке сайта.
        # Пользователь сможет продолжить работу (если хватает прав) даже со сломанным профилем.
        return {"name": "Гость", "username": "guest", "avatar_url": ""}
        