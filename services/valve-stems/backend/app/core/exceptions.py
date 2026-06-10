"""
Доменные исключения (Domain Exceptions).

Содержит кастомную иерархию ошибок бизнес-логики.
Использование собственных исключений позволяет изолировать слой
математических расчетов и работы с БД от транспортного слоя (FastAPI).
Все исключения из этого модуля перехватываются централизованно
в `error_handlers.py` и преобразуются в соответствующие HTTP-ответы.
"""


class AppBaseError(Exception):
    """
    Базовый класс всех доменных ошибок приложения.
    
    Гарантирует, что у любой ошибки всегда есть человекочитаемое
    сообщение (`message`) и системные детали (`details`) для логирования.
    """

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class EntityNotFoundError(AppBaseError):
    """
    Запрошенная сущность не найдена в БД.
    Обычно преобразуется в HTTP 404 (Not Found).
    """

    def __init__(self, entity_name: str, entity_id: int | str):
        super().__init__(
            message=f"{entity_name} с ID={entity_id} не найден(а) в справочнике.",
            details=f"entity={entity_name}, id={entity_id}",
        )


class ValidationError(AppBaseError):
    """
    Ошибка валидации входных данных (бизнес-логика).
    Обычно преобразуется в HTTP 422 (Unprocessable Entity).
    
    Наследует сигнатуру инициализации от AppBaseError: 
    требует передачи `message` и опционального `details`.
    """

    pass


class UnitConversionError(AppBaseError):
    """
    Ошибка конвертации единиц измерения.
    Срабатывает, если библиотека uniconv не знает переданную величину.
    Обычно преобразуется в HTTP 400 (Bad Request).
    """

    def __init__(self, field: str, unit: str):
        super().__init__(
            message=f"Неизвестная единица измерения '{unit}' для поля '{field}'.",
            details=f"field={field}, unit={unit}",
        )


class PhysicsCalculationError(AppBaseError):
    """
    Ошибка в физическом расчёте.
    Срабатывает при математических коллизиях (отрицательный корень, 
    неверные перепады давления, деление на ноль в формулах).
    """

    pass


class SteamPropertiesError(AppBaseError):
    """
    Ошибка получения свойств воды/пара из IAPWS/SEUIF97.
    Срабатывает, если термодинамические параметры выходят за рамки таблиц.
    """

    def __init__(
        self,
        pressure: float,
        temperature: float | None = None,
        enthalpy: float | None = None,
    ):
        params = f"P={pressure} МПа"
        if temperature is not None:
            params += f", T={temperature} °C"
        if enthalpy is not None:
            params += f", H={enthalpy} кДж/кг"
            
        super().__init__(
            message=f"Не удалось определить свойства пара при заданных параметрах ({params}). "
            f"Проверьте корректность введённых давления и температуры/энтальпии.",
            details=params,
        )
        