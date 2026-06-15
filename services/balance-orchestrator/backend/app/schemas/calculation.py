"""
Схемы данных для сохранения результатов расчетов.

Этот модуль содержит Pydantic-модели, используемые для валидации
и сериализации данных перед их сохранением в базу данных 
или внешние системы оркестрации (например, привязка к Issue в GitLab).
Обеспечивает строгую типизацию входящих JSON-запросов.
"""

from typing import Any

from pydantic import BaseModel, Field


class CalculationSaveRequest(BaseModel):
    """
    Модель запроса для сохранения результатов математического расчета.

    Attributes:
        task_iid (int): Внутренний идентификатор задачи.
        project_id (int): Идентификатор проекта, к которому относится расчет.
        app_type (str): Идентификатор расчетного модуля.
        input_data (dict[str, Any]): JSON-объект с входными параметрами.
        output_data (dict[str, Any]): JSON-объект с результатами вычисления.
        commit_message (str | None): Опциональное описание сохранения.
    """

    # [ENGINEERING CONTEXT]
    # Почему используется Field: это позволяет "прокинуть" описания (description) 
    # и примеры (examples) напрямую в автогенерируемый Swagger UI, 
    # не меняя при этом бизнес-логику валидации (поля остаются строго обязательными).
    
    task_iid: int = Field(
        ..., 
        description="Внутренний идентификатор задачи (Issue IID), к которой привязан расчет.",
        examples=[1054]
    )
    
    project_id: int = Field(
        ..., 
        description="Уникальный идентификатор проекта.",
        examples=[42]
    )
    
    app_type: str = Field(
        ..., 
        description="Тип приложения или расчетного модуля (например, 'valves' или 'condenser').",
        examples=["valves"]
    )
    
    input_data: dict[str, Any] = Field(
        ..., 
        description="Словарь с входными параметрами расчета (сырые данные, конфигурация).",
        examples=[{"flow_rate": 15.5, "inlet_pressure": 101325}]
    )
    
    output_data: dict[str, Any] = Field(
        ..., 
        description="Словарь с результатами математического вычисления.",
        examples=[{"heat_transfer_coefficient": 4500.0, "is_critical": False}]
    )
    
    commit_message: str | None = Field(
        None, 
        description="Опциональное сообщение коммита для ведения истории версий расчета.",
        examples=["Обновлен расчет с учетом новых данных по давлению"]
    )
    