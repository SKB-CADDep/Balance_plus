"""
ORM-модель турбин (Turbines).

Описывает справочник уникальных турбин и их связь (Many-to-Many) 
с клапанами (штоками) в базе данных PostgreSQL.
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.core.database import Base

# Промежуточная таблица (Association Table) для реализации связи Many-to-Many 
# между турбинами и клапанами (штоками).
# Использование ondelete="CASCADE" гарантирует, что при удалении турбины 
# связи автоматически очистятся, предотвращая появление "сиротских" записей.
turbine_valve_link = Table(
    "turbine_valve_link",
    Base.metadata,
    Column(
        "turbine_id", 
        Integer, 
        ForeignKey("autocalc.unique_turbine.id", ondelete="CASCADE"), 
        primary_key=True
    ),
    Column(
        "valve_id", 
        Integer, 
        ForeignKey("autocalc.stocks.id", ondelete="CASCADE"), 
        primary_key=True
    ),
    schema="autocalc"
)


class Turbine(Base):
    """
    Таблица 'unique_turbine' в схеме 'autocalc'.
    Хранит информацию о турбинах (станция, заводской номер).
    """
    __tablename__ = "unique_turbine"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)

    station_name = Column(String, nullable=True, index=True)
    station_number = Column(String, nullable=True)
    factory_number = Column(String, unique=True, index=True, nullable=True)

    # Двунаправленная связь Многие-ко-Многим с моделью Valve (штоки)
    valves = relationship(
        "Valve", 
        secondary=turbine_valve_link, 
        back_populates="turbines"
    )

    def __repr__(self):
        # WARNING (Технический долг):
        # Статичный __repr__ может стать неудобным при добавлении новых колонок.
        # В будущем рекомендуется вынести генерацию __repr__ в базовый класс (Base).
        return f"<Turbine(name='{self.name}', station='{self.station_name}')>"
        