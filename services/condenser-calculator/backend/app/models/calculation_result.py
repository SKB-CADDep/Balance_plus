"""
ORM-модель для хранения результатов вычислений (Архив расчетов).

Связывает входные параметры, выбранную методику расчета и итоговые 
результаты (матрицы). Обеспечивает воспроизводимость расчетов и 
формирует историческую базу для аналитики.
"""

import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.condenser import Condenser


class CalculationResult(Base):
    """
    Таблица 'calculation_results'.
    Хранит лог выполненных расчетов конденсаторов.
    """
    __tablename__ = "calculation_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        doc="Уникальный идентификатор (суррогатный ключ) записи расчета."
    )

    condenser_id: Mapped[int] = mapped_column(
        ForeignKey("condensers.id", ondelete="CASCADE"),
        index=True,
        doc="Внешний ключ на справочник оборудования (конденсаторы)."
    )

    method: Mapped[str] = mapped_column(
        String(50), 
        index=True,
        doc="Методика расчета, использованная математическим ядром (например, 'berman' или 'metro-vickers')."
    )

    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        doc="Сырой JSON входящего запроса (состояние параметров на момент расчета для обеспечения воспроизводимости)."
    )
    
    output_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        doc="Сырой JSON ответа ядра (рассчитанные матрицы, давления, характеристики эжекторов и телеметрия)."
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        doc="Временная метка создания записи (UTC). Используется для сортировки истории."
    )

    # --- Связи (Relationships) ---
    
    condenser: Mapped["Condenser"] = relationship(
        back_populates="calculations",
        doc="Связь с объектом Condenser. Позволяет получать данные оборудования через result.condenser"
    )
    