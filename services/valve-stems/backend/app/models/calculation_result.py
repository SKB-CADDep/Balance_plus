from sqlalchemy import JSON, Column, DateTime, Integer, String, func

from app.core.database import Base


class CalculationResultDB(Base):
    # Оставляем имя класса для Alembic/SQLAlchemy, если ты используешь Base.
    # Если у тебя класс называется просто CalculationResultDB (без BaseModel),
    # используй свой стандартный синтаксис.
    __tablename__ = "calculation_results"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=True)

    # Сюда будем писать: "БТ-252380 (2шт) + БТ-281220 (4шт)"
    stock_name = Column(String, nullable=False)

    turbine_name = Column(String, nullable=False)

    calc_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)

    # УДАЛЕНО: valve_id = Column(Integer, ForeignKey("autocalc.stocks.id"))
    # УДАЛЕНО: valve = relationship("Valve", back_populates="calculation_results")
