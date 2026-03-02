from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.core.database import Base

# Таблица-связка для реализации Many-to-Many
turbine_valve_link = Table(
    "turbine_valve_link",
    Base.metadata,
    Column("turbine_id", Integer, ForeignKey("autocalc.unique_turbine.id", ondelete="CASCADE"), primary_key=True),
    Column("valve_id", Integer, ForeignKey("autocalc.stocks.id", ondelete="CASCADE"), primary_key=True),
    schema="autocalc"
)

class Turbine(Base):
    __tablename__ = "unique_turbine"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True) 
    
    station_name = Column(String, nullable=True, index=True)
    station_number = Column(String, nullable=True)
    factory_number = Column(String, unique=True, index=True, nullable=True)

    # Связь с клапанами через промежуточную таблицу
    valves = relationship("Valve", secondary=turbine_valve_link, back_populates="turbines")

    def __repr__(self):
        return f"<Turbine(name='{self.name}', station='{self.station_name}')>"
