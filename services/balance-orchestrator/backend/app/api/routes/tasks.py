# api/routes/tasks.py
import gitlab.exceptions
from fastapi import APIRouter, HTTPException, Query
from slugify import slugify

from app.core.gitlab_adapter import gitlab_client
from app.schemas.task import BranchCreateRequest, BranchInfo, TaskCreate, TaskInfo


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskInfo])
async def list_tasks(
    project_id: int = Query(..., description="ID проекта обязателен"), # Делаем обязательным для 422
    state: str = "opened", 
    my_only: bool = False
):
    """
    Получить список задач.
    - state: opened, closed, all
    - my_only: только мои задачи
    """
    try:
        # Передаем project_id в адаптер (если адаптер поддерживает фильтрацию)
        # Если нет, просто оставляем для валидации запроса
        issues = gitlab_client.get_all_assigned_issues(state=state)
        return issues
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения задач: {e}")


@router.get("/{issue_iid}", response_model=TaskInfo)
async def get_task(issue_iid: int, project_id: int = Query(...)):
    """Получить задачу по номеру"""
    try:
        issue = gitlab_client.get_issue(issue_iid, project_id)
        return issue
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabGetError:
        raise HTTPException(status_code=404, detail=f"Задача #{issue_iid} не найдена в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения задачи: {e}")


@router.post("", response_model=TaskInfo)
async def create_task(task: TaskCreate):
    """Создать новую задачу"""
    try:
        issue_data = gitlab_client.create_issue(
            title=task.title,
            description=task.description,
            labels=task.labels,
            project_id=task.project_id  # Передаем ID проекта
        )

        # Возвращаем полную информацию через get_issue
        return gitlab_client.get_issue(issue_data["iid"], issue_data["project_id"])
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabGetError:
        raise HTTPException(status_code=404, detail="Проект не найден в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания задачи: {e}")


@router.post("/{issue_iid}/branch", response_model=BranchInfo)
async def create_task_branch(issue_iid: int, payload: BranchCreateRequest):
    """
    Создать ветку для работы над задачей.
    Имя ветки: issue/{iid}-{transliterated-slug}
    """
    try:
        project_id = payload.project_id

        # Получаем информацию о задаче
        issue = gitlab_client.get_issue(issue_iid, project_id)

        # 1. Генерируем безопасный slug (кириллица -> латиница, пробелы -> дефисы)
        # Пример: "Тестовый расчёт" -> "testovyi-raschet"
        safe_slug = slugify(issue["title"], max_length=40)

        # Если заголовок был из одних спецсимволов, slug может быть пустым
        if not safe_slug:
            safe_slug = "task"

        branch_name = f"issue/{issue_iid}-{safe_slug}"

        print(f"🛠 Пытаемся создать ветку: {branch_name}") # Лог для отладки

        # Создаём ветку
        created = gitlab_client.create_branch(branch_name, project_id=project_id)

        return BranchInfo(
            branch_name=branch_name,
            issue_iid=issue_iid,
            created=created,
        )
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabGetError:
        raise HTTPException(status_code=404, detail="Задача или проект не найдены в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        # Логируем ошибку подробнее
        print(f"❌ Ошибка создания ветки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания ветки: {e}")


@router.post("/{issue_iid}/submit")
async def submit_task(issue_iid: int, project_id: int = Query(...)):
    try:
        # 1. Получаем информацию о задаче
        issue = gitlab_client.get_issue(issue_iid, project_id)

        # 2. НАДЕЖНЫЙ ПОИСК ВЕТКИ
        branch_name = gitlab_client.find_branch_by_issue_iid(issue_iid, project_id)

        if not branch_name:
             # Фоллбек: если ветки нет, попробуем сгенерировать (вдруг еще не создана?)
             # Но для сабмита это странно. Лучше вернуть ошибку.
             raise HTTPException(
                 status_code=400,
                 detail=f"Ветка для задачи #{issue_iid} не найдена в GitLab. Сначала нажмите 'Начать работу'."
             )

        print(f"📌 Найдена ветка для сабмита: {branch_name}")

        # 3. Формируем заголовок MR
        mr_title = f"Draft: Решение задачи #{issue_iid}: {issue['title']}"
        mr_desc = f"Автоматически созданный MR из Balance+ IDE.\nCloses #{issue_iid}"

        # 4. Создаем MR
        result = gitlab_client.create_merge_request(
            source_branch=branch_name,
            title=mr_title,
            description=mr_desc,
            project_id=project_id
        )

        return {"status": "success", "mr_url": result["web_url"], "mr_iid": result["iid"]}

    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabGetError:
        raise HTTPException(status_code=404, detail="Задача или ветка не найдены в GitLab")
    except gitlab.exceptions.GitlabError as e:
        # Ловим ошибку "MR already exists" и красиво отдаем
        if "already exists" in str(e):
            raise HTTPException(status_code=400, detail="Merge Request уже создан!")
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except HTTPException:
        raise
    except Exception as e:
        # Ловим ошибку "MR already exists" и красиво отдаем
        if "already exists" in str(e):
             raise HTTPException(status_code=400, detail="Merge Request уже создан!")
        raise HTTPException(status_code=500, detail=f"Ошибка создания MR: {e}")
