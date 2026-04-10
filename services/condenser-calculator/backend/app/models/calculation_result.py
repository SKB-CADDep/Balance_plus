from datetime import datetime
from sqlalchemy import String, JSON, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class CalculationResult(Base):
    __tablename__ = "calculation_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Связь с конденсатором
    condenser_id: Mapped[int] = mapped_column(Integer, ForeignKey("condensers.id"), index=True)
    
    method: Mapped[str] = mapped_column(String(50))
    
    input_data: Mapped[dict] = mapped_column(JSON)
    output_data: Mapped[dict] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )