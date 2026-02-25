from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Turbine(Base):
    __tablename__ = "unique_turbine"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Название модели (напр. Т-110/120...) больше не уникально глобально
    name = Column(String, nullable=False, index=True) 
    
    # Новые поля для конкретизации проекта
    station_name = Column(String, nullable=True, index=True) # Название станции
    station_number = Column(String, nullable=True)           # Станционный номер
    factory_number = Column(String, unique=True, index=True, nullable=True) # Заводской номер (обычно уникален)

    valves = relationship("Valve", back_populates="turbine", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Turbine(name='{self.name}', station='{self.station_name}')>"
