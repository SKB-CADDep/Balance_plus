class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_uuid = Column(String, unique=True)             # UUID из JSON
    name = Column(String, nullable=False)                   # "12МХЛ", "Л-68"
    
    # λ = f(t): массив точек [[t1, λ1], [t2, λ2], ...]
    thermal_conductivity_points = Column(JSON, nullable=False)
    
    # Полный JSON материала (для будущих расчётов, где нужны другие свойства)
    full_properties = Column(JSON)