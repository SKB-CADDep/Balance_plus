class CondenserBaseError(Exception):
    """Базовое доменное исключение."""


class EntityNotFoundError(CondenserBaseError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class MaterialPropertyError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}. Причина: {self.details}"
        return self.message


class UnitConversionError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}. Причина: {self.details}"
        return self.message


class CalculationEngineError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}. Причина: {self.details}"
        return self.message


class ValidationError(CondenserBaseError):
    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}. Причина: {self.details}"
        return self.message
