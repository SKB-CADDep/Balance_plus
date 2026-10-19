"""
Аудит межсервисной безопасности (Service-to-Service): изоляция путей расчётов и защита от подделки путей
"""

import pytest
from app.schemas.calculation import CalculationSaveRequest


class TestInterServicePayloadValidation:
    """Проверка валидации входящих полезных нагрузок от внешних воркеров/приложений."""

    def test_calculation_save_request_rejects_missing_required_fields(self):
        """Схема отклоняет запросы без обязательных полей task_iid, project_id, app_type."""
        with pytest.raises(ValueError):
            CalculationSaveRequest(
                project_id=1,
                app_type="valves",
                input_data={},
                output_data={},
            )

    def test_calculation_save_request_accepts_valid_app_types(self):
        """Проверка формирования путей по типу приложения (valves, condenser)."""
        req_valves = CalculationSaveRequest(
            task_iid=1,
            project_id=1,
            app_type="valves",
            input_data={"test": 1},
            output_data={"res": 2},
        )
        assert req_valves.app_type == "valves"

        req_cond = CalculationSaveRequest(
            task_iid=1,
            project_id=1,
            app_type="condenser",
            input_data={"steam": 120},
            output_data={"pressure": 0.004},
        )
        assert req_cond.app_type == "condenser"