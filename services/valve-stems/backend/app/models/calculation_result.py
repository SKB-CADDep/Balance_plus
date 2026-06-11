"""
ORM-модель для хранения результатов вычислений (Calculation Results).

Хранит полный слепок (snapshot) входных параметров и полученных результатов
в формате JSON для ведения истории (Архив расчетов). 
Отвязана от строгих внешних ключей (Foreign Keys) оборудования, 
чтобы гарантировать сохранность исторических данных даже при удалении
исходного оборудования из справочников.
"""

from sqlalchemy import JSON, Column, DateTime, Integer, String, func

from app.core.database import Base


class CalculationResultDB(Base):
    """
    Таблица 'calculation_results' в схеме 'autocalc'.
    Хранит историю расчетов штоков клапанов.
    """
    __tablename__ = "calculation_results"
    __table_args__ = {"schema": "autocalc"}

    # WARNING (Технический долг):
    # Используется синтаксис SQLAlchemy 1.x (Column). В будущем рекомендуется 
    # миграция на аннотации Mapped[int] = mapped_column(...) для поддержки SA 2.0.

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=True, doc="Имя пользователя, запустившего расчет")

    # Составное имя, например: "БТ-252380 (2шт) + БТ-281220 (4шт)"
    stock_name = Column(
        String, 
        nullable=False, 
        doc="Строковое представление участвовавших в расчете клапанов и их количества"
    )

    turbine_name = Column(String, nullable=False, doc="Наименование турбины")

    calc_timestamp = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        doc="Метка времени (UTC) завершения расчета"
    )
    
    # JSON-слепки данных (позволяют хранить вложенные структуры без жестких схем)
    input_data = Column(JSON, nullable=False, doc="Слепок входных параметров (MultiCalculationParams)")
    output_data = Column(JSON, nullable=False, doc="Слепок выходных результатов (MultiCalculationResult)")
    