"""
Иерархия доменных (кастомных) исключений микросервиса.

Модуль определяет классы ошибок, специфичные для бизнес-логики расчетного ядра 
и работы с базой данных. Использование собственных исключений позволяет 
контроллерам (роутерам) и глобальным обработчикам (Exception Handlers) 
перехватывать ожидаемые сбои и формировать для фронтенда понятные JSON-ответы, 
вместо стандартной 500-й ошибки сервера.
"""


class CondenserBaseError(Exception):
    """
    Базовое доменное исключение.
    
    Все кастомные ошибки сервиса должны наследоваться от этого класса. 
    Это позволяет перехватить любую бизнес-ошибку одним блоком 
    `except CondenserBaseError`.
    """


class EntityNotFoundError(CondenserBaseError):
    """
    Исключение: Сущность не найдена в базе данных.
    
    Выбрасывается слоем CRUD (например, при поиске конденсатора или материала), 
    если запрошенный ID или UUID отсутствует в PostgreSQL. Обычно приводит 
    к HTTP-статусу 404 (Not Found).
    """
    def __init__(self, message: str):
        """
        Args:
            message (str): Человекочитаемое сообщение об ошибке.
        """
        super().__init__(message)
        self.message = message


class MaterialPropertyError(CondenserBaseError):
    """
    Исключение: Ошибка свойств трубного материала.
    
    Выбрасывается, если данные материала повреждены или их недостаточно 
    для выполнения математических расчетов (например, пустая таблица теплопроводности).
    """
    def __init__(self, message: str, details: str | None = None):
        """
        Args:
            message (str): Основное сообщение (например, "Недостаточно точек данных").
            details (str | None): Дополнительная техническая информация (например, ID материала).
        """
        super().__init__(message)
        self.message = message
        self.details = details


class UnitConversionError(CondenserBaseError):
    """
    Исключение: Ошибка конвертации физических величин.
    
    Выбрасывается конвертером (UnitConverter), если запрошена неизвестная единица 
    измерения, или математическим адаптером при неудачной попытке привести 
    данные (например, энтальпию) к базовым единицам ядра. Обычно приводит 
    к HTTP-статусу 422 (Unprocessable Entity).
    """
    def __init__(self, message: str, details: str | None = None):
        """
        Args:
            message (str): Описание проблемы конвертации.
            details (str | None): Дополнительный контекст (например, переданное значение).
        """
        super().__init__(message)
        self.message = message
        self.details = details


class CalculationEngineError(CondenserBaseError):
    """
    Исключение: Критический сбой математического ядра.
    
    Выбрасывается слоем адаптеров или стратегий, если расчет не сошелся 
    (например, метод Ньютона превысил лимит итераций, или произошло деление на ноль). 
    Обычно приводит к HTTP-статусу 400 (Bad Request).
    """
    def __init__(self, message: str, details: str | None = None):
        """
        Args:
            message (str): Общее сообщение о сбое ядра.
            details (str | None): Трассировка или конкретная математическая причина.
        """
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(CondenserBaseError):
    """
    Исключение: Ошибка бизнес-валидации.
    
    Выбрасывается валидаторами (например, BR-02), если переданные данные 
    физически несовместимы с выбранной методикой (отсутствует нужное число 
    ходов пучка и т.д.). Обычно приводит к HTTP-статусу 422 (Unprocessable Entity).
    """
    def __init__(self, message: str, details: str | None = None):
        """
        Args:
            message (str): Указание на нарушенное бизнес-правило (например, BR-02).
            details (str | None): Подробный список нарушений (каких полей не хватает).
        """
        super().__init__(message)
        self.message = message
        self.details = details
        