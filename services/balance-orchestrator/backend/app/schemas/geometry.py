# schemas/geometry.py

"""
Схемы данных для описания геометрических характеристик оборудования.

Этот модуль содержит Pydantic-модели для валидации и сериализации
геометрических параметров (размеры, материалы, метаданные). Используется
для строгой типизации конфигураций конденсаторов и генерации манифестов.
"""

from pydantic import BaseModel, Field


class GeometryInfo(BaseModel):
    """
    Краткая информация о геометрии для отображения в списках.

    Используется в реестрах, где требуется только базовая метаинформация 
    (без загрузки тяжеловесных данных о каждой трубке и размере).

    Attributes:
        id (str): Уникальный строковый идентификатор геометрии.
        name (str): Человекочитаемое название.
        type (str): Тип оборудования.
        description (str | None): Дополнительное описание (опционально).
        file (str): Имя или путь к файлу с полными данными.
    """
    id: str = Field(
        ..., 
        description="Уникальный строковый идентификатор геометрии.", 
        examples=["geom_001"]
    )
    name: str = Field(
        ..., 
        description="Человекочитаемое название геометрии для UI.", 
        examples=["Конденсатор 100-КПЦ"]
    )
    type: str = Field(
        ..., 
        description="Категория или тип оборудования.", 
        examples=["condenser"]
    )
    description: str | None = Field(
        None, 
        description="Дополнительная техническая информация или комментарии к модели.", 
        examples=["Базовая геометрия для турбины К-300"]
    )
    file: str = Field(
        ..., 
        description="Путь или имя файла (JSON/YAML), содержащего полную структуру геометрии.", 
        examples=["condenser_k300.json"]
    )


class GeometriesManifest(BaseModel):
    """
    Манифест со списком всех доступных геометрий в системе.

    Attributes:
        schema_version (str): Версия схемы манифеста.
        geometries (list[GeometryInfo]): Массив кратких описаний доступных геометрий.
    """
    schema_version: str = Field(
        ..., 
        description="Версия структуры данных манифеста (для контроля обратной совместимости).", 
        examples=["1.0.0"]
    )
    geometries: list[GeometryInfo] = Field(
        ..., 
        description="Список всех зарегистрированных в системе базовых геометрий."
    )


class Dimension(BaseModel):
    """
    Универсальная модель для описания физической величины с указанием размерности.

    Attributes:
        value (float): Численное значение величины.
        unit (str): Строковое обозначение единицы измерения.
    """
    
    # [ENGINEERING CONTEXT]
    # Почему используется разделение на `value` и `unit`, а не просто float:
    # Это защищает математическое ядро от скрытых ошибок размерностей.
    # Жестко требуя передачи единиц измерения (например, 'mm' вместо 'm'), 
    # мы можем конвертировать величины "на лету" перед передачей в расчетный движок.
    
    value: float = Field(
        ..., 
        description="Численное значение физической величины.", 
        examples=[12.5]
    )
    unit: str = Field(
        ..., 
        description="Единица измерения по системе СИ или производная (например, 'm', 'mm').", 
        examples=["m"]
    )


class CondenserDimensions(BaseModel):
    """
    Детализированные геометрические размеры конденсатора.

    Attributes:
        length (Dimension): Длина аппарата.
        diameter (Dimension): Внешний или внутренний диаметр корпуса.
        tube_count (int): Общее количество охлаждающих трубок в пучке.
        tube_diameter (Dimension): Диаметр одной охлаждающей трубки.
    """
    length: Dimension = Field(
        ..., 
        description="Полная рабочая длина корпуса конденсатора."
    )
    diameter: Dimension = Field(
        ..., 
        description="Диаметр корпуса конденсатора."
    )
    tube_count: int = Field(
        ..., 
        description="Общее количество охлаждающих трубок в трубном пучке.", 
        examples=[15340]
    )
    tube_diameter: Dimension = Field(
        ..., 
        description="Диаметр одной охлаждающей трубки."
    )


class CondenserMaterials(BaseModel):
    """
    Материалы, используемые в конструкции конденсатора.

    Attributes:
        shell (str): Материал корпуса аппарата.
        tubes (str): Материал охлаждающих трубок.
    """
    shell: str = Field(
        ..., 
        description="Марка или тип материала корпуса.", 
        examples=["Ст3сп", "Углеродистая сталь"]
    )
    tubes: str = Field(
        ..., 
        description="Марка или тип материала охлаждающих трубок.", 
        examples=["МНЖ5-1", "Титан ВТ1-0"]
    )


class CondenserGeometry(BaseModel):
    """
    Полная геометрия конденсатора.

    Агрегирует идентификационные данные, размеры и материалы,
    необходимые для проведения тепло-гидравлических расчетов аппарата.

    Attributes:
        id (str): Идентификатор полной геометрии.
        type (str): Тип геометрии.
        version (str): Версия конкретной геометрии.
        dimensions (CondenserDimensions): Блок с геометрическими размерами.
        materials (CondenserMaterials): Блок с описанием материалов конструкции.
    """
    id: str = Field(
        ..., 
        description="Уникальный строковый идентификатор данной геометрии.", 
        examples=["condenser_v1_main"]
    )
    type: str = Field(
        ..., 
        description="Тип оборудования.", 
        examples=["condenser"]
    )
    version: str = Field(
        ..., 
        description="Версия набора геометрических данных (для отслеживания изменений).", 
        examples=["1.0.2"]
    )
    dimensions: CondenserDimensions = Field(
        ..., 
        description="Комплекс геометрических размеров корпуса и трубного пучка."
    )
    materials: CondenserMaterials = Field(
        ..., 
        description="Спецификация материалов, из которых изготовлен конденсатор."
    )
    