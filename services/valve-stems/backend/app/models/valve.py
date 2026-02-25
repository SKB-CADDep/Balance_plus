from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Valve(Base):
    __tablename__ = "stocks"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True)
    # УБРАЛИ unique=True, так как один чертеж может быть у разных турбин
    name = Column(String, nullable=False, index=True) 
    type = Column(String, nullable=True) # 'СК', 'РК', 'СРК' или полное название
    diameter = Column(Float, nullable=True)
    clearance = Column(Float, nullable=True)
    count_parts = Column(Integer, nullable=True)
    len_part1 = Column(Float, nullable=True)
    len_part2 = Column(Float, nullable=True)
    len_part3 = Column(Float, nullable=True)
    len_part4 = Column(Float, nullable=True)
    len_part5 = Column(Float, nullable=True)
    round_radius = Column(Float, nullable=True)

    turbine_id = Column(Integer, ForeignKey("autocalc.unique_turbine.id"), nullable=False)

    turbine = relationship("Turbine", back_populates="valves")
    calculation_results = relationship("CalculationResultDB", back_populates="valve")

    def __repr__(self):
        return f"<Valve(name='{self.name}', type='{self.type}')>"
