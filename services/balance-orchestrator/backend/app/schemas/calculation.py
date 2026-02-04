from typing import Any

from pydantic import BaseModel


class CalculationSaveRequest(BaseModel):
    task_iid: int
    project_id: int
    app_type: str            # например 'valves'
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    commit_message: str | None = "Сохранение результатов расчёта"
