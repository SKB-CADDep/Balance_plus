"""
Pydantic-схемы для унификации ответов с ошибками.

Обеспечивает единый формат JSON-ответов при возникновении 
бизнес-исключений (EntityNotFoundError), ошибок валидации (ValidationError) 
или внутренних сбоев математического ядра.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    """
    Стандартная модель ответа при HTTP-ошибках (4xx, 5xx).
    
    Используется глобальными обработчиками исключений FastAPI для 
    формирования предсказуемой структуры ответа для клиентских приложений.
    """
    
    error: str = Field(
        ..., 
        description="Технический тип или код ошибки (например, 'CalculationEngineError', 'NotFound')"
    )
    message: str = Field(
        ..., 
        description="Человекочитаемое сообщение об ошибке, которое можно показать пользователю"
    )
    details: Optional[str] = Field(
        default=None, 
        description="Дополнительные технические детали для отладки (стек-трейс, дампы, причины валидации)"
    )