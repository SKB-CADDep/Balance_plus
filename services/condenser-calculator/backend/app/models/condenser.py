"""
ORM-модель оборудования (Конденсаторы).

Хранит паспортные, геометрические и конструктивные характеристики
паротурбинных конденсаторов. Эти данные выступают базовым шаблоном (const)
для математического ядра при расчете режимов работы.
"""

from typing import Any, TYPE_CHECKING

from sqlalchemy import String, JSON, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Предотвращаем цикличные импорты между связными таблицами
if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.calculation_result import CalculationResult


# 1. Промежуточная таблица для связи "Многие-ко-Многим" (Конденсатор <-> Материал)
# По стандарту SA 2.0 такие таблицы-связки остаются объектами Table.
condenser_material_association = Table(
    "condenser_material_association",
    Base.metadata,
    Column("condenser_id", ForeignKey("condensers.id", ondelete="CASCADE"), primary_key=True),
    Column("material_id", ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True),
    info={"doc": "Таблица-связка допустимых материалов для конкретной модели конденсатора."}
)


class Condenser(Base):
    """
    Таблица 'condensers'. 
    Справочник оборудования (конденсаторных установок).
    """
    __tablename__ = "condensers"

    # --- Базовая идентификация ---
    
    id: Mapped[int] = mapped_column(
        primary_key=True,
        doc="Внутренний ID аппарата в базе данных."
    )
    
    name_condenser: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True,
        doc="Марка/Наименование конденсатора (например, 'К-800-2' или '100-КЦС-4')."
    )
    
    # Использование `str | None` автоматически делает колонку `nullable=True`
    project_id: Mapped[str | None] = mapped_column(String(50), doc="Шифр проекта или чертежа")
    doc_num_thermo_calc: Mapped[str | None] = mapped_column(String(50), doc="Номер теплового расчета")
    doc_num_assembly: Mapped[str | None] = mapped_column(String(50), doc="Номер сборочного чертежа")
    doc_num_passport: Mapped[str | None] = mapped_column(String(50), doc="Номер паспорта оборудования")

    # --- Геометрия (Трубные пучки) ---
    
    # Если тип просто float (а не float | None), колонка автоматически становится NOT NULL
    diameter_internal: Mapped[float] = mapped_column(doc="Внутренний диаметр охлаждающих трубок (мм).")
    wall_thickness: Mapped[float] = mapped_column(doc="Толщина стенки охлаждающих трубок (мм).")

    main_length: Mapped[float] = mapped_column(doc="Длина трубок ОСНОВНОГО пучка (мм).")
    main_count: Mapped[int] = mapped_column(doc="Количество трубок ОСНОВНОГО пучка (шт).")
    
    builtin_length: Mapped[float | None] = mapped_column(doc="Длина трубок ВСТРОЕННОГО пучка (мм).")
    builtin_count: Mapped[int | None] = mapped_column(doc="Количество трубок ВСТРОЕННОГО пучка (шт).")
    
    aircooler_count: Mapped[int | None] = mapped_column(doc="Количество трубок воздухоохладителя (шт).")

    # --- Конструктивные параметры (Гидравлика и Эжекция) ---
    
    passes_main: Mapped[int] = mapped_column(doc="Число ходов основной охлаждающей воды (Z_main).")
    passes_builtin: Mapped[int | None] = mapped_column(doc="Число ходов во встроенном пучке (Z_builtin).")
    ejectors_count: Mapped[int] = mapped_column(doc="Штатное количество эжекторов (шт).")

    # --- Номинальные / Расчетные режимы ---
    
    mass_flow_steam_nom: Mapped[float] = mapped_column(doc="Номинальный расход пара (т/ч).")
    mass_flow_air: Mapped[float] = mapped_column(doc="Нормативный расход присосов воздуха (кг/ч).")
    
    water_flow_limits: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, 
        doc="JSON с ограничениями расходов воды. Пример: {'min': 4000, 'max': 9000, 'step': 1000}."
    )

    # =================================================================
    # СВЯЗИ (RELATIONSHIPS)
    # =================================================================
    
    # 2. Связь Many-to-Many с материалами
    # Обратите внимание на типизацию Mapped[list["Material"]]
    materials: Mapped[list["Material"]] = relationship(
        secondary=condenser_material_association, 
        back_populates="condensers",
        doc="Список трубных сплавов, допустимых для данной модели конденсатора."
    )

    # 3. Связь One-to-Many с результатами расчетов
    calculations: Mapped[list["CalculationResult"]] = relationship(
        back_populates="condenser", 
        cascade="all, delete-orphan",
        doc="Архив всех расчетов, произведенных для этого аппарата."
    )