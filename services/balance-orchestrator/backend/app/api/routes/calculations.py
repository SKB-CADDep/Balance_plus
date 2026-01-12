import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.schemas.calculation import CalculationSaveRequest
from app.core.gitlab_adapter import gitlab_client
from slugify import slugify

router = APIRouter(prefix="/calculations", tags=["Calculations"])


@router.post("/save")
async def save_calculation_result(req: CalculationSaveRequest):
    """
    Сохраняет результаты расчёта в ветку задачи.
    """
    try:
        # 1. Ищем РЕАЛЬНУЮ ветку задачи (Умный поиск)
        # Передаем project_id, так как мы теперь в мульти-репо
        branch_name = gitlab_client.find_branch_by_issue_iid(req.task_iid, req.project_id)
        
        if not branch_name:
             raise HTTPException(status_code=400, detail=f"Ветка для задачи #{req.task_iid} не найдена в GitLab. Убедитесь, что работа над задачей начата.")

        print(f"💾 Сохраняем в ветку: {branch_name} (Проект ID: {req.project_id})")

        # 2. Формируем путь
        ts_str = req.output_data.get('calc_timestamp') or datetime.now().isoformat()
        folder_name = ts_str.replace(':', '-').replace('.', '-')
        base_path = f"calculations/{req.app_type}/{folder_name}"
        
        # 3. Готовим файлы
        files_to_commit = {
            f"{base_path}/input.json": json.dumps(req.input_data, indent=2, ensure_ascii=False),
            f"{base_path}/result.json": json.dumps(req.output_data, indent=2, ensure_ascii=False)
        }

        # 4. Коммитим (с указанием project_id!)
        commit = gitlab_client.create_commit_multiple(
            files=files_to_commit,
            commit_message=f"Calc Result: {req.commit_message}",
            branch=branch_name,
            project_id=req.project_id # <--- Важно!
        )

        return {
            "status": "saved", 
            "commit_id": commit.id, 
            "path": base_path,
            "web_url": commit.web_url
        }

    except Exception as e:
        print(f"Error saving calculation: {e}")
        # Если это HTTPException, пробрасываем его как есть
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_calculation(task_iid: int = Query(...), app_type: str = Query(...), project_id: int = Query(...)):
    """
    Возвращает данные последнего расчёта для гидрации формы.
    """
    try:
        # 1. Определяем ветку
        issue = gitlab_client.get_issue(task_iid, project_id)
        safe_slug = slugify(issue["title"], max_length=40) or "task"
        branch_name = f"issue/{task_iid}-{safe_slug}"
        
        if not gitlab_client.branch_exists(branch_name, project_id=project_id):
            return {"found": False, "reason": "Branch not found"}

        # 2. Ищем папку с расчётами
        base_path = f"calculations/{app_type}"
        folders = gitlab_client.list_files_in_path(base_path, ref=branch_name, project_id=project_id)
        
        if not folders:
            return {"found": False, "reason": "No calculations found"}
            
        # 3. Сортируем папки (они у нас ISO timestamp, так что сортировка по алфавиту сработает)
        # folder['name'] выглядит как '2025-11-27T10-00-00'
        folders.sort(key=lambda x: x['name'], reverse=True)
        latest_folder = folders[0]['name']
        
        full_path = f"{base_path}/{latest_folder}"
        
        # 4. Читаем файлы
        input_content = gitlab_client.get_file_content_decoded(f"{full_path}/input.json", ref=branch_name, project_id=project_id)
        result_content = gitlab_client.get_file_content_decoded(f"{full_path}/result.json", ref=branch_name, project_id=project_id)
        
        if not input_content:
             return {"found": False, "reason": "Files missing"}

        return {
            "found": True,
            "timestamp": latest_folder,
            "input_data": json.loads(input_content),
            "output_data": json.loads(result_content) if result_content else None
        }

    except Exception as e:
        print(f"Error getting calc: {e}")
        # Не падаем с ошибкой, а просто говорим "данных нет", чтобы форма открылась пустой
        return {"found": False, "error": str(e)}