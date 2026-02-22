from typing import Any
from pydantic import BaseModel, model_validator
from app.core.uniconv_adapter import convert_input_data_units

class CalculationSaveRequest(BaseModel):
    task_iid: int
    project_id: int
    app_type: str            # например 'valves'
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    commit_message: str | None = "Сохранение результатов расчёта"

    @model_validator(mode="after")
    def unify_units(self) -> 'CalculationSaveRequest':
        """
        Хук Pydantic: автоматически приводит все единицы измерения 
        во входящих данных к эталонным (ТЗ) перед обработкой запроса.
        """
        if self.input_data:
            try:
                self.input_data = convert_input_data_units(self.input_data)
            except Exception as e:
                # Если frontend прислал неизвестную единицу, вернется 422 Unprocessable Entity
                raise ValueError(f"Ошибка конвертации единиц измерения: {e}")
        return self