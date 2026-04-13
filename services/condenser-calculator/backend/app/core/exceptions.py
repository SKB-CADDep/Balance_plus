class AppBaseError(Exception):
    """Базовый класс всех ошибок приложения."""
    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class EntityNotFoundError(AppBaseError):
    """Сущность не найдена в БД."""
    pass


class ValidationError(AppBaseError):
    """Ошибка бизнес-валидации."""
    pass


class UnitConversionError(AppBaseError):
    """Ошибка конвертации единиц."""
    pass


class MaterialPropertyError(AppBaseError):
    """Ошибка работы с свойствами материала (λ(t) и т.д.)."""
    pass


class CalculationEngineError(AppBaseError):
    """Ошибка в математическом ядре."""
    pass