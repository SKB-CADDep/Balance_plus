"""
Роутер для управления задачами (Tasks).
В рамках архитектуры "Git-as-a-Database", задачи (Tasks) маппятся на GitLab Issues, 
рабочие пространства — на Git Branches, а отправка на проверку — на Merge Requests.
"""
# api/routes/tasks.py
import gitlab.exceptions
from fastapi import APIRouter, HTTPException, Query, Path
from slugify import slugify

from app.core.gitlab_adapter import gitlab_client
from app.schemas.task import BranchCreateRequest, BranchInfo, TaskCreate, TaskInfo


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "", 
    response_model=list[TaskInfo],
    summary="Получение списка задач (Issues)",
    response_description="Массив объектов задач с учетом фильтрации"
)
async def list_tasks(
    project_id: int = Query(..., title="ID Проекта", description="ID проекта обязателен для фильтрации"), 
    state: str = Query("opened", title="Состояние задачи", description="Статус: 'opened', 'closed' или 'all'"), 
    my_only: bool = Query(False, title="Только мои", description="Фильтр: вернуть только задачи, назначенные на текущего пользователя")
):
    """
    Получает список задач (GitLab Issues) для выбранного проекта.

    Args:
        project_id (int): Уникальный идентификатор проекта в GitLab.
        state (str): Фильтр по статусу задачи (opened/closed/all).
        my_only (bool): Флаг для фильтрации задач по assignee.

    Returns:
        list[TaskInfo]: Список задач, валидированных через Pydantic.

    Raises:
        HTTPException (401, 502, 500): Ошибки авторизации, API GitLab или внутреннего сервера.
    """
    try:
        # [ENGINEERING CONTEXT]
        # Валидация на уровне эндпоинта (FastAPI Query):
        # Передаем project_id в адаптер (если адаптер поддерживает фильтрацию).
        # Явное требование project_id = Query(...) на уровне роута гарантирует 
        # возврат чистой ошибки 422 Unprocessable Entity от FastAPI до того, 
        # как запрос уйдет в GitLab и упадет там с ошибкой 500.
        issues = gitlab_client.get_all_assigned_issues(state=state, project_id=project_id)
        return issues
    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения задач: {e}")


@router.get(
    "/{issue_iid}", 
    response_model=TaskInfo,
    summary="Получение детальной информации о задаче",
    response_description="Объект конкретной задачи из GitLab"
)
async def get_task(
    issue_iid: int = Path(..., title="Номер задачи", description="Внутренний IID задачи (Issue) в рамках проекта"), 
    project_id: int = Query(..., title="ID Проекта", description="Уникальный идентификатор проекта")
):
    """
    Получает конкретную задачу по её внутреннему номеру (IID).

    Args:
        issue_iid (int): Номер (Issue IID) задачи.
        project_id (int): ID проекта, которому принадлежит задача.

    Returns:
        TaskInfo: Полная информация о задаче.

    Raises:
        HTTPException (404): Если задача с таким IID не найдена в проекте.
        HTTPException (401, 502, 500): Ошибки инфраструктуры и API.
    """
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


@router.post(
    "", 
    response_model=TaskInfo,
    summary="Создание новой задачи (Issue)",
    response_description="Объект успешно созданной задачи"
)
async def create_task(task: TaskCreate):
    """
    Создает новую задачу (GitLab Issue) в указанном проекте.

    Args:
        task (TaskCreate): Тело запроса с названием, описанием и метками (labels).

    Returns:
        TaskInfo: Полный объект созданной задачи (включая сгенерированный IID).

    Raises:
        HTTPException (404): Если целевой проект не найден.
        HTTPException (401, 502, 500): Ошибки инфраструктуры и API.
    """
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


@router.post(
    "/{issue_iid}/branch", 
    response_model=BranchInfo,
    summary="Создание Git-ветки для работы над задачей",
    response_description="Метаданные созданной ветки (название, дата создания)"
)
async def create_task_branch(
    issue_iid: int = Path(..., title="Номер задачи", description="IID задачи, к которой привязывается ветка"), 
    payload: BranchCreateRequest = ...
):
    """
    Создает новую ветку в репозитории для изоляции расчетов по задаче.

    Формирует стандартизированное имя ветки формата `issue/{iid}-{transliterated-slug}`.

    Args:
        issue_iid (int): Номер задачи для интеграции в имя ветки.
        payload (BranchCreateRequest): Данные запроса (ID проекта).

    Returns:
        BranchInfo: Информационный объект о созданной ветке.

    Raises:
        HTTPException (404): Если задача или проект не найдены.
        HTTPException (500): При сбоях генерации ветки.
    """
    try:
        project_id = payload.project_id

        # Получаем информацию о задаче
        issue = gitlab_client.get_issue(issue_iid, project_id)

        # [ENGINEERING CONTEXT]
        # Зачем нужен slugify (транслитерация и удаление пробелов):
        # Пользователи создают задачи на русском языке (кириллица, спецсимволы). 
        # Git-клиенты и ядро GitLab имеют строгие ограничения на именование веток 
        # (запрет на пробелы, проблемы с кодировками кириллицы в некоторых ОС).
        # slugify превращает "Тестовый расчёт!" в безопасное "testovyi-raschet", 
        # гарантируя, что ветка будет валидной с точки зрения протокола Git.
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


@router.post(
    "/{issue_iid}/submit",
    summary="Отправка задачи на проверку (Создание Merge Request)",
    response_description="Статус операции и ссылка на созданный MR"
)
async def submit_task(
    issue_iid: int = Path(..., title="Номер задачи", description="IID задачи для формирования MR"), 
    project_id: int = Query(..., title="ID Проекта", description="Идентификатор проекта в GitLab")
):
    """
    Отправляет результаты задачи на ревью путем создания Merge Request (MR).

    Находит рабочую ветку задачи, формирует драфт (Draft) MR с привязкой 
    закрытия задачи (Closes #IID) и отправляет запрос в GitLab API.

    Args:
        issue_iid (int): Номер (IID) задачи.
        project_id (int): Идентификатор проекта.

    Returns:
        dict: Статус успешного создания с веб-ссылкой (web_url) и IID MR.

    Raises:
        HTTPException (400): Если ветка не существует (работа не начата) 
            или MR уже был создан ранее.
        HTTPException (401, 404, 502, 500): Стандартные ошибки API.
    """
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
        # [ENGINEERING CONTEXT]
        # Паттерн "String matching" для ошибок API:
        # Библиотека python-gitlab при попытке создать дубликат MR возвращает общую ошибку
        # GitlabCreateError (409 Conflict) без уникального класса исключения для дубликатов.
        # Поэтому мы используем хак: парсим `str(e)` в поиске подстроки "already exists",
        # чтобы перехватить эту специфичную бизнес-ситуацию и отдать фронтенду 400 Bad Request
        # со внятным русским текстом, вместо страшной ошибки 502.
        
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
        