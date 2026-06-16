"""
Роутер для управления жизненным циклом расчётов.
Отвечает за сохранение и получение результатов вычислений, используя GitLab 
в качестве единого источника истины (Git-as-a-Database).
"""
import json

import gitlab
import gitlab.exceptions
from fastapi import APIRouter, HTTPException, Query

from app.core.gitlab_adapter import gitlab_client
from app.schemas.calculation import CalculationSaveRequest


router = APIRouter(prefix="/calculations", tags=["Calculations"])


@router.post(
    "/save",
    summary="Сохранение результатов расчёта",
    response_description="Успешный статус сохранения с деталями созданного коммита"
)
async def save_calculation_result(req: CalculationSaveRequest):
    """
    Сохраняет входные данные и результаты расчёта в репозиторий GitLab.

    Взаимодействует с GitLab API для поиска ветки, привязанной к задаче, 
    и создает коммит с файлами `input.json` и `result.json` в фиксированной директории.

    Args:
        req (CalculationSaveRequest): Валидированная Pydantic-схема с данными расчёта,
            содержащая ID проекта, задачи, входные и выходные параметры.

    Returns:
        dict: Словарь с информацией об успешном сохранении:
            - status (str): Статус операции (всегда "saved").
            - commit_id (str): Хеш созданного коммита.
            - path (str): Базовый путь в репозитории, куда сохранены файлы.
            - web_url (str): Прямая ссылка на коммит в GitLab для просмотра.

    Raises:
        HTTPException (400): Если ветка для задачи не найдена (работа не начата) 
            или возникла ошибка доступа к проекту.
        HTTPException (401): При недействительном токене GitLab.
        HTTPException (404): Если целевой объект не найден в GitLab.
        HTTPException (502): При проблемах на стороне шлюза/API GitLab.
        HTTPException (500): При непредвиденных внутренних ошибках сервера.
    """
    try:
        # 1. Поиск ветки.
        try:
            branch_name = gitlab_client.find_branch_by_issue_iid(req.task_iid, req.project_id)
        except (gitlab.exceptions.GitlabError, Exception) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка доступа к GitLab или проекту: {str(e)}"
            )

        if not branch_name:
            raise HTTPException(
                status_code=400,
                detail=f"Ветка для задачи #{req.task_iid} не найдена в GitLab. Убедитесь, что работа над задачей начата."
            )

        # 2. Подготовка данных (используем .get() для commit_message)
        req_data = req.model_dump()
        msg = req_data.get("commit_message") or "Результаты расчёта"
        
        # [ENGINEERING CONTEXT]
        # Почему мы используем фиксированный путь `calculations/{req.app_type}/current`:
        # GitLab выступает в роли NoSQL-хранилища для состояния расчетов. 
        # Использование папки /current гарантирует, что при загрузке формы (hydration) 
        # мы всегда будем брать актуальный срез данных (head) без необходимости 
        # хранить маппинг "коммит <-> расчет" в отдельной СУБД. 
        # Версионирование обеспечивается самой историей Git (Git history).
        base_path = f"calculations/{req.app_type}/current"

        files_to_commit = {
            f"{base_path}/input.json": json.dumps(req.input_data, indent=2, ensure_ascii=False),
            f"{base_path}/result.json": json.dumps(req.output_data, indent=2, ensure_ascii=False)
        }

        # 3. Коммит
        commit = gitlab_client.create_commit_multiple(
            files=files_to_commit,
            commit_message=f"Calc Result: {msg}",
            branch=branch_name,
            project_id=req.project_id
        )

        return {
            "status": "saved",
            "commit_id": commit.id,
            "path": base_path, 
            "web_url": commit.web_url
        }

    except gitlab.exceptions.GitlabAuthenticationError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации в GitLab")
    except gitlab.exceptions.GitlabGetError:
        raise HTTPException(status_code=404, detail="Объект не найден в GitLab")
    except gitlab.exceptions.GitlabError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка GitLab API: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.get(
    "/latest",
    summary="Загрузка последних данных расчёта",
    response_description="Структура данных для гидрации фронтенд-формы (без вызова HTTP-ошибок)"
)
async def get_latest_calculation(
    task_iid: int = Query(..., title="ID Задачи", description="IID Issue в GitLab (внутренний номер задачи)"), 
    app_type: str = Query(..., title="Тип приложения", description="Идентификатор типа расчёта/модуля"), 
    project_id: int = Query(..., title="ID Проекта", description="Уникальный идентификатор проекта в GitLab")
):
    """
    Возвращает данные последнего расчёта для гидрации формы на клиенте.
    
    Осуществляет "умный поиск" ветки по IID задачи и читает содержимое файлов 
    `input.json` и `result.json` напрямую из репозитория GitLab по фиксированному пути 
    `calculations/{app_type}/current/`.

    Args:
        task_iid (int): Номер задачи для поиска привязанной ветки.
        app_type (str): Тип приложения, определяющий директорию хранения.
        project_id (int): ID проекта в GitLab для доступа к репозиторию.

    Returns:
        dict: Объект, описывающий результат поиска:
            - found (bool): Флаг наличия сохраненных данных.
            - input_data (dict, optional): Входные параметры (если найдены).
            - output_data (dict, optional): Результаты расчёта (если найдены).
            - reason/error (str, optional): Системная причина отсутствия данных для дебага.
    """
    try:
        # 1. Ищем РЕАЛЬНУЮ ветку задачи (Умный поиск)
        branch_name = gitlab_client.find_branch_by_issue_iid(
            task_iid, project_id)

        if not branch_name:
            return {"found": False, "reason": "Branch not found"}

        # 2. Читаем файлы напрямую из фиксированного пути
        base_path = f"calculations/{app_type}/current"
        input_content = gitlab_client.get_file_content_decoded(
            f"{base_path}/input.json", ref=branch_name, project_id=project_id)
        result_content = gitlab_client.get_file_content_decoded(
            f"{base_path}/result.json", ref=branch_name, project_id=project_id)

        if not input_content:
            return {"found": False, "reason": "Files missing"}

        return {
            "found": True,
            "input_data": json.loads(input_content),
            "output_data": json.loads(result_content) if result_content else None
        }

    except gitlab.exceptions.GitlabAuthenticationError:
        return {"found": False, "error": "Ошибка авторизации в GitLab"}
    except gitlab.exceptions.GitlabGetError:
        return {"found": False, "reason": "Branch or files not found"}
    except gitlab.exceptions.GitlabError as e:
        return {"found": False, "error": f"Ошибка GitLab API: {e}"}
    except Exception as e:
        print(f"Error getting calc: {e}")
        # [ENGINEERING CONTEXT]
        # Запрет на прерывание потока (Swallowing exceptions):
        # В отличие от эндпоинта /save, здесь мы намеренно перехватываем ВСЕ исключения
        # и возвращаем {"found": False} с HTTP статусом 200 OK (без raise HTTPException).
        # Почему это сделано так: если пользователь впервые открывает задачу (файлов в Git еще нет), 
        # генерация 404/500 ошибки "сломает" страницу на фронтенде. Возврат `found: False` 
        # сообщает фронтенду штатно отрендерить пустую форму ввода данных для старта работы.
        return {"found": False, "error": str(e)}
        