from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Project(Base):
    """
    Проект = Экземпляр оборудования (конкретная турбина на конкретной станции).
    Аналог Equipment в твоем примере.
    """
    __tablename__ = 'projects'
    __table_args__ = (
        # Заводской номер должен быть уникальным (или уникальным в рамках типа, зависит от бизнес-логики)
        # Сделаем уникальным глобально для надежности
        UniqueConstraint('factory_number', name='uq_project_factory_number'),
        {'schema': 'autocalc'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Ссылка на тип турбины (справочник геометрии)
    turbine_id = Column(Integer, ForeignKey('autocalc.unique_turbine.id'), nullable=False)

    # Метаданные проекта
    station_name = Column(String, nullable=False, index=True, comment="Название станции (ТЭЦ/ГРЭС)")
    factory_number = Column(String, nullable=False, unique=True, index=True, comment="Заводской номер")
    station_number = Column(String, nullable=True, comment="Станционный номер")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Связи
    turbine = relationship("Turbine", backref="projects")  # backref создаст projects в модели Turbine

    # calculation_results = relationship("MultiCalculationResultDB", back_populates="project") # Добавим позже

    def __repr__(self):
        return f"<Project(id={self.id}, station='{self.station_name}', num='{self.factory_number}')>"