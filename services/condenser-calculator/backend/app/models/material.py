from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    # BR-12
    thermal_properties = Column(JSON, nullable=True)

    # Обратная связь
    condensers = relationship("Condenser", back_populates="material")
