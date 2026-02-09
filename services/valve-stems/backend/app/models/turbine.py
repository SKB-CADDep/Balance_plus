from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Turbine(Base):
    __tablename__ = "unique_turbine"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)

    valves = relationship("Valve", back_populates="turbine")

    def __repr__(self):
        return f"<Turbine(name='{self.name}')>"