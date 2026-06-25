from sqlalchemy import Column, Integer, String, JSON, text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_uuid = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, unique=True)

    # λ = f(t): массив точек [[t1, λ1], [t2, λ2], ...]
    thermal_conductivity_points = Column(JSON, nullable=False)

    # Полный JSON материала (для будущих расчётов)
    full_properties = Column(JSON)

    condensers = relationship(
        "Condenser", 
        secondary="condenser_material_association", 
        back_populates="materials"
    )