"""
ORM-модель клапанов/штоков (Valves).

Описывает справочник геометрических параметров штоков клапанов,
которые выступают исходными данными для физического математического ядра.
"""

from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Valve(Base):
    """
    Таблица 'stocks' в схеме 'autocalc'.
    Хранит геометрию конкретного чертежа штока клапана.
    """
    __tablename__ = "stocks"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True)
    
    # Строгое бизнес-правило: имя чертежа должно быть уникальным
    # для предотвращения коллизий при выборе параметров для расчета.
    name = Column(String, nullable=False, unique=True, index=True, doc="Номер чертежа")

    type = Column(String, nullable=True, doc="Тип клапана")
    diameter = Column(Float, nullable=True, doc="Диаметр (мм/м - зависит от логики парсера)")
    clearance = Column(Float, nullable=True, doc="Зазор")
    count_parts = Column(Integer, nullable=True, doc="Количество геометрических участков (от 2 до 5)")
    
    # Геометрия по участкам
    len_part1 = Column(Float, nullable=True)
    len_part2 = Column(Float, nullable=True)
    len_part3 = Column(Float, nullable=True)
    len_part4 = Column(Float, nullable=True)
    len_part5 = Column(Float, nullable=True)
    
    round_radius = Column(Float, nullable=True, doc="Радиус скругления")

    # Двунаправленная связь Многие-ко-Многим с моделью Turbine
    # Используется строковое указание secondary для избежания циклических импортов
    turbines = relationship(
        "Turbine", 
        secondary="autocalc.turbine_valve_link", 
        back_populates="valves"
    )

    def __repr__(self):
        # WARNING (Технический долг):
        # В будущем рекомендуется вынести генерацию __repr__ в базовый класс (Base).
        return f"<Valve(name='{self.name}', type='{self.type}')>"
        