from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Condenser(Base):
    __tablename__ = "condensers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 2.1 Основная информация
    name_condenser = Column(String, nullable=False, unique=True, index=True)
    project_id = Column(String)  # ID проекта (String для гибкости)
    doc_num_thermo_calc = Column(String)
    doc_num_assembly = Column(String)
    doc_num_passport = Column(String)

    # Геометрия
    diameter_internal = Column(Float, nullable=False)  # мм
    wall_thickness = Column(Float, nullable=False)  # мм
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)

    main_length = Column(Float, nullable=False)  # мм
    main_count = Column(Integer, nullable=False)  # шт
    builtin_length = Column(Float)  # мм (может быть NULL)
    builtin_count = Column(Integer)  # шт
    aircooler_count = Column(Integer)  # шт

    passes_main = Column(Integer, nullable=False)  # >= 1
    passes_builtin = Column(Integer)  # >= 1
    ejectors_count = Column(Integer, nullable=False)  # >= 1

    # Паспортные ограничения (Limits)
    mass_flow_steam_nom = Column(Float, nullable=False)  # кг/ч
    mass_flow_air = Column(Float, nullable=False)  # кг/ч

    # BR-06 и BR-07: Все лимиты расходов воды в одном JSON (min/max)
    water_flow_limits = Column(JSON)

    # Relationship
    material = relationship("Material", back_populates="condensers")

    calculations = relationship("CalculationResult", back_populates="condenser", cascade="all, delete-orphan")
