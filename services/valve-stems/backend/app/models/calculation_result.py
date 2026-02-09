from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class CalculationResultDB(Base):
    __tablename__ = "resultcalcs"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=True)
    stock_name = Column(String, nullable=False)
    turbine_name = Column(String, nullable=False)
    calc_timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)

    valve_id = Column(Integer, ForeignKey("autocalc.stocks.id"), nullable=False)

    valve = relationship("Valve", back_populates="calculation_results")

    def __repr__(self):
        return f"<CalculationResultDB(stock_name='{self.stock_name}', turbine_name='{self.turbine_name}')>"