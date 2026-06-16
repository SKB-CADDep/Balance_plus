"""
Роутер для работы с проектами.
Отвечает за проксирование запросов к GitLab API для получения списка проектов,
с которыми может взаимодействовать текущий пользователь.
"""
# api/routes/projects.py
import gitlab.exceptions
from fastapi import APIRouter, HTTPException, Query

from app.core.gitlab_adapter import gitlab_client


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    summary="Получение списка проектов",
    response_description="Массив объектов проектов GitLab, доступных пользователю"
)
async def list_projects(
    search: str = Query(
        "", 
        title="Поисковый запрос", 
        description="Подстрока для фильтрации проектов по их названию или пути"
    )
):
    """
    Запрашивает список проектов GitLab для выбора при создании новой задачи.

    Функция обращается к GitLab API от имени системного клиента (или пользователя) 
    и возвращает список проектов, соответствующих переданной строке поиска.

    Args:
        search (str): Строка поиска. Если передана пустая строка (по умолчанию), 
            возвращается список всех доступных проектов.

    Returns:
        list[dict]: Список словарей (объектов) с метаданными проектов из GitLab 
            (содержит id, name, path_with_namespace и т.д.).

    Raises:
        HTTPException (401): Если токен доступа к GitLab недействителен или отсутствует.
        HTTPException (502): При таймауте или внутренней ошибке на серверах GitLab (Bad Gateway).
        HTTPException (500): При ошибках маппинга данных или других системных сбоях.
    """
    try:
        # [ENGINEERING CONTEXT]
        # Паттерн делегирования фильтрации (Push-down filter):
        # Мы намеренно передаем параметр `search` прямо в gitlab_client, а не 
        # выгружаем список всех проектов (list_all) для последующей фильтрации in-memory в Python.
        # Почему это важно: у пользователя или системного токена может быть доступ 
        # к тысячам проектов. Загрузка всех данных в оперативную память оркестратора 
        # приведет к просадке производительности и риску утечки памяти (OOM - Out of Memory).
        # GitLab API эффективно фильтрует данные на уровне своей базы данных.
        return gitlab_client.get_user_projects(search)
        
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка проектов: {e}")
        