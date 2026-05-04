from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[str] = None