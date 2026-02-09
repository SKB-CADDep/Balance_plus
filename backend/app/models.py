from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Turbine(Base):
    __tablename__ = 'unique_turbine'
    __table_args__ = {'schema': 'autocalc'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)

    # Связь с Valve
    valves = relationship("Valve", back_populates="turbine")

    def __repr__(self):
        return f"<Turbine(name='{self.name}')>"


class Valve(Base):
    __tablename__ = 'stocks'
    __table_args__ = {'schema': 'autocalc'}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(String, nullable=True)
    diameter = Column(Float, nullable=True)
    clearance = Column(Float, nullable=True)
    count_parts = Column(Integer, nullable=True)
    len_part1 = Column(Float, nullable=True)
    len_part2 = Column(Float, nullable=True)
    len_part3 = Column(Float, nullable=True)
    len_part4 = Column(Float, nullable=True)
    len_part5 = Column(Float, nullable=True)
    round_radius = Column(Float, nullable=True)

    # Внешний ключ на UniqueTurbine
    turbine_id = Column(Integer, ForeignKey('autocalc.unique_turbine.id'), nullable=False)

    # Связь с Turbine
    turbine = relationship("Turbine", back_populates="valves")

    # Связь с CalculationResultDB
    calculation_results = relationship("CalculationResultDB", back_populates="valve")

    def __repr__(self):
        return f"<Valve(name='{self.name}', valve_type='{self.type}')>"


class CalculationResultDB(Base):
    __tablename__ = 'resultcalcs'
    __table_args__ = {'schema': 'autocalc'}

    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=True)
    stock_name = Column(String, nullable=False)
    turbine_name = Column(String, nullable=False)
    calc_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)

    # Внешний ключ на Valve - обязательно применять на бд
    valve_id = Column(Integer, ForeignKey('autocalc.stocks.id'), nullable=False)

    # Связь с Valve
    valve = relationship("Valve", back_populates="calculation_results")

    def __repr__(self):
        return f"<CalculationResultDB(stock_name='{self.stock_name}', turbine_name='{self.turbine_name}')>"
