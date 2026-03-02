from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

class Valve(Base):
    __tablename__ = "stocks"
    __table_args__ = {"schema": "autocalc"}

    id = Column(Integer, primary_key=True)
    # Имя чертежа теперь СТРОГО УНИКАЛЬНО! Никаких дублей.
    name = Column(String, nullable=False, unique=True, index=True) 
    
    type = Column(String, nullable=True)
    diameter = Column(Float, nullable=True)
    clearance = Column(Float, nullable=True)
    count_parts = Column(Integer, nullable=True)
    len_part1 = Column(Float, nullable=True)
    len_part2 = Column(Float, nullable=True)
    len_part3 = Column(Float, nullable=True)
    len_part4 = Column(Float, nullable=True)
    len_part5 = Column(Float, nullable=True)
    round_radius = Column(Float, nullable=True)

    # Связь обратно к турбинам
    turbines = relationship("Turbine", secondary="autocalc.turbine_valve_link", back_populates="valves")
    

    def __repr__(self):
        return f"<Valve(name='{self.name}', type='{self.type}')>"
