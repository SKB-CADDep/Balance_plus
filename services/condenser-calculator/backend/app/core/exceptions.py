class CondenserBaseError(Exception):
    """Базовое доменное исключение."""


class EntityNotFoundError(CondenserBaseError):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class MaterialPropertyError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class UnitConversionError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class CalculationEngineError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details

class ValidationError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details
