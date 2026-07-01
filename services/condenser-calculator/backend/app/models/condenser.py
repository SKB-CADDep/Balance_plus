from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from app.models.base import Base

# 1. Создаем промежуточную таблицу для связи Многие-ко-Многим
condenser_material_association = Table(
    "condenser_material_association",
    Base.metadata,
    Column("condenser_id", Integer, ForeignKey("condensers.id", ondelete="CASCADE"), primary_key=True),
    Column("material_id", Integer, ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True)
)

class Condenser(Base):
    __tablename__ = "condensers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_condenser = Column(String, nullable=False, unique=True, index=True)
    project_id = Column(String)
    doc_num_thermo_calc = Column(String)
    doc_num_assembly = Column(String)
    doc_num_passport = Column(String)

    # Геометрия
    diameter_internal = Column(Float, nullable=False)
    wall_thickness = Column(Float, nullable=False)

    main_length = Column(Float, nullable=False)
    main_count = Column(Integer, nullable=False)
    builtin_length = Column(Float)
    builtin_count = Column(Integer)
    aircooler_count = Column(Integer)

    passes_main = Column(Integer, nullable=False)
    passes_builtin = Column(Integer)
    ejectors_count = Column(Integer, nullable=False)

    mass_flow_steam_nom = Column(Float, nullable=False)
    mass_flow_air = Column(Float, nullable=False)
    water_flow_limits = Column(JSON)

    # 2. Обновляем связь на Many-to-Many с использованием secondary
    materials = relationship(
        "Material", 
        secondary=condenser_material_association, 
        back_populates="condensers"
    )

    calculations = relationship("CalculationResult", back_populates="condenser", cascade="all, delete-orphan")