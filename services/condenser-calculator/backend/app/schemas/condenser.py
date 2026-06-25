"""
Pydantic-схемы для сущности «Конденсатор».

Определяют контракты данных для справочника оборудования. 
Разделяют представление на базовое (для списков/поиска) и детальное 
(полная геометрия аппарата, необходимая для запуска математического ядра).
Используются для автоматической валидации и сериализации ORM-моделей (SQLAlchemy) в JSON.
"""

from pydantic import ConfigDict, BaseModel, Field
from typing import Optional, List

from app.schemas.material import MaterialShort


class CondenserBase(BaseModel):
    """
    Базовая схема конденсатора.
    
    Содержит общие идентификационные атрибуты, которые наследуются 
    остальными схемами (как для краткого, так и для детального ответа).
    """
    name_condenser: str = Field(..., description="Наименование (маркировка) конденсатора")
    project_name: Optional[str] = Field(None, description="Название проекта или объекта установки")


class CondenserListItem(CondenserBase):
    """
    Схема для элемента списка конденсаторов (краткое представление).
    
    Используется в эндпоинте GET /condensers для минимизации объема 
    передаваемых данных по сети (без тяжелых массивов геометрии).
    """
    id: int

    model_config = ConfigDict(from_attributes=True)


class CondenserDetail(CondenserBase):
    """
    Детальная схема конденсатора.
    
    Содержит полную спецификацию аппарата: геометрию трубных пучков, 
    номинальные расходы и вложенные связи (материалы). Эта модель возвращается
    при запросе конкретного аппарата и передается в расчетное ядро.
    """
    id: int
    
    # Геометрия трубок
    diameter_internal: float = Field(..., description="Внутренний диаметр трубок (мм или м в зависимости от БД)")
    wall_thickness: float = Field(..., description="Толщина стенки трубок")
    
    # Связи с другими сущностями
    materials: List[MaterialShort] = Field(
        default_factory=list, 
        description="Связанный список материалов труб, доступных для расчета этого аппарата"
    )
    
    # Параметры основного пучка
    main_length: float = Field(..., description="Рабочая длина трубок основного пучка")
    main_count: int = Field(..., description="Количество трубок основного пучка")
    passes_main: int = Field(..., description="Число ходов охлаждающей воды в основном пучке")
    
    # Параметры встроенного пучка (опционально, есть не у всех конденсаторов)
    builtin_length: Optional[float] = Field(None, description="Рабочая длина трубок встроенного пучка")
    builtin_count: Optional[int] = Field(None, description="Количество трубок встроенного пучка")
    passes_builtin: Optional[int] = Field(None, description="Число ходов воды во встроенном пучке")
    
    # Вспомогательное оборудование и телеметрия
    aircooler_count: Optional[int] = Field(None, description="Количество трубок воздухоохладителя")
    ejectors_count: int = Field(..., description="Штатное количество эжекторов")
    
    # Номинальные расходы (паспортные данные)
    mass_flow_steam_nom: float = Field(..., description="Номинальный расход пара")
    mass_flow_air: float = Field(..., description="Номинальный расход присосов воздуха")
    
    # Ограничения для расчетов
    water_flow_limits: Optional[dict] = Field(None, description="Допустимые диапазоны расходов охлаждающей воды")

    model_config = ConfigDict(from_attributes=True)


# Алиас для удобного импорта в других модулях (например, в роутерах)
CondenserShort = CondenserListItem
