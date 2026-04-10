import uuid
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # UUID генерируется автоматически при создании
    uuid: Mapped[str] = mapped_column(
        String(36), 
        default=lambda: str(uuid.uuid4()), 
        unique=True, 
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), index=True)
    
    properties: Mapped[dict | None] = mapped_column(JSON)