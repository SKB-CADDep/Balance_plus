from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str  # Кодовое название ошибки
    message: str  # Текст сообщения
    details: str | None = None  # Технические детали
    request_id: str | None = None
