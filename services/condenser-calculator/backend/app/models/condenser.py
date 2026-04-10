from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Condenser(Base):
    __tablename__ = "condensers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name_condenser: Mapped[str] = mapped_column(String(255), index=True)
    
    project_name: Mapped[str | None] = mapped_column(String(255), index=True)
    
    geometry_data: Mapped[dict | None] = mapped_column(JSON)