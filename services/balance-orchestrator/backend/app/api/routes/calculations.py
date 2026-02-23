import json
import gitlab.exceptions
from fastapi import APIRouter, HTTPException, Query

from app.core.gitlab_adapter import gitlab_client
from app.schemas.calculation import CalculationSaveRequest

router = APIRouter(prefix="/calculations", tags=["Calculations"])

@router.post("/save")
async def save_calculation_result(req: CalculationSaveRequest):
    """
    Сохраняет результаты расчёта в ветку задачи.
    Входящие параметры УЖЕ конвертированы в базовые ед. изм.
    """
    try:
        branch_name = gitlab_client.find_branch_by_issue_iid(req.task_iid, req.project_id)

        if not branch_name:
            raise HTTPException(
                status_code=400,
                detail=f"Ветка для задачи #{req.task_iid} не найдена в GitLab."
            )

        print(f"💾 Сохраняем в ветку: {branch_name} (Проект ID: {req.project_id})")

        base_path = f"calculations/{req.app_type}/current"
        
        files_to_commit = {
            f"{base_path}/input.json": json.dumps(req.input_data, indent=2, ensure_ascii=False),
            f"{base_path}/result.json": json.dumps(req.output_data, indent=2, ensure_ascii=False)
        }

        commit = gitlab_client.create_commit_multiple(
            files=files_to_commit,
            commit_message=f"Calc Result: {req.commit_message}",
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
        print(f"Error saving calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_calculation(task_iid: int = Query(...), app_type: str = Query(...), project_id: int = Query(...)):
    """
    Возвращает данные последнего расчёта для гидрации формы.
    Читает из фиксированного пути calculations/{app_type}/current/
    """
    try:
        # 1. Ищем РЕАЛЬНУЮ ветку задачи (Умный поиск)
        branch_name = gitlab_client.find_branch_by_issue_iid(task_iid, project_id)

        if not branch_name:
            return {"found": False, "reason": "Branch not found"}

        # 2. Читаем файлы напрямую из фиксированного пути
        base_path = f"calculations/{app_type}/current"
        input_content = gitlab_client.get_file_content_decoded(f"{base_path}/input.json", ref=branch_name, project_id=project_id)
        result_content = gitlab_client.get_file_content_decoded(f"{base_path}/result.json", ref=branch_name, project_id=project_id)

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
        # Не падаем с ошибкой, а просто говорим "данных нет", чтобы форма открылась пустой
        return {"found": False, "error": str(e)}
