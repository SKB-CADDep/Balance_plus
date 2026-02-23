from typing import Any, Dict
from pydantic import BaseModel, model_validator

from uniconv import UnknownUnitError, UnknownParameterError
from app.core.uniconv_adapter import convert_input_data_units

class CalculationSaveRequest(BaseModel):
    task_iid: int
    project_id: int
    app_type: str
    input_data: Dict[str, Any]  # Используем Dict, так как корневой объект JSON — это {}
    output_data: Dict[str, Any]
    commit_message: str | None = "Сохранение результатов расчёта"

    @model_validator(mode="after")
    def unify_units(self) -> 'CalculationSaveRequest':
        """
        Автоматически приводит единицы измерения к эталонным.
        """
        if self.input_data:
            try:
                self.input_data = convert_input_data_units(self.input_data)
            
            except UnknownUnitError as e:
                raise ValueError(f"Неизвестная единица измерения во входных данных: {e}")
            
            except UnknownParameterError as e:
                raise ValueError(f"Неизвестный тип параметра: {e}")
                
            except Exception as e:
                raise ValueError(f"Критическая ошибка при обработке данных: {e}")
                
        return self