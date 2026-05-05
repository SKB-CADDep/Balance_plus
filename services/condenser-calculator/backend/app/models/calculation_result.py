# app/models/calculation_result.py

from datetime import datetime

from sqlalchemy import String, JSON, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class CalculationResult(Base):
    __tablename__ = "calculation_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    condenser_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("condensers.id"),
        index=True,
        nullable=False,
    )

    method: Mapped[str] = mapped_column(String(50), index=True)

    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    condenser = relationship("Condenser", back_populates="calculations")