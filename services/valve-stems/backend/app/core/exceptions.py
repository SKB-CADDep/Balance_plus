class AppBaseError(Exception):
    """Базовый класс всех доменных ошибок приложения."""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class EntityNotFoundError(AppBaseError):
    """Запрошенная сущность не найдена в БД."""

    def __init__(self, entity_name: str, entity_id: int | str):
        super().__init__(
            message=f"{entity_name} с ID={entity_id} не найден(а) в справочнике.",
            details=f"entity={entity_name}, id={entity_id}",
        )


class ValidationError(AppBaseError):
    """Ошибка валидации входных данных (бизнес-логика)."""

    pass


class UnitConversionError(AppBaseError):
    """Ошибка конвертации единиц измерения."""

    def __init__(self, field: str, unit: str):
        super().__init__(
            message=f"Неизвестная единица измерения '{unit}' для поля '{field}'.",
            details=f"field={field}, unit={unit}",
        )


class PhysicsCalculationError(AppBaseError):
    """Ошибка в физическом расчёте (отрицательный корень, неверные перепады и т.п.)."""

    pass


class SteamPropertiesError(AppBaseError):
    """Ошибка получения свойств воды/пара из IAPWS/SEUIF97."""

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
