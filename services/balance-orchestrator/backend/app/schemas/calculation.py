from pydantic import BaseModel
from typing import Any, Dict, Optional

class CalculationSaveRequest(BaseModel):
    task_iid: int
    project_id: int
    app_type: str            # например 'valves'
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    commit_message: Optional[str] = "Сохранение результатов расчёта"