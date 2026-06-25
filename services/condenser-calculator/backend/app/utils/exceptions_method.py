"""
Модуль обработки исключительных (нестандартных) сценариев расчета давления.

Содержит бизнес-логику для определения давления в конденсаторе в ситуациях, 
когда стандартный тепловой расчет не требуется. Например, когда давление 
явно задано пользователем или берется из альтернативных параметров (PIF).
"""

class CondenserExceptions:
    """
    Определяет приоритет выбора значения давления в конденсаторе.
    
    Используется в случаях, когда алгоритм должен решить, брать ли давление 
    напрямую из входных данных (bypass расчета), или возвращать None, 
    чтобы сигнализировать о необходимости полноценного математического расчета.
    """

    def __init__(self, pressure_condenser: float | None, temperature_cooling_water_1: float | None, pif: float | None):
        """
        Инициализирует класс набором входных параметров.

        Args:
            pressure_condenser (float | None): Явно заданное абсолютное давление в конденсаторе.
            temperature_cooling_water_1 (float | None): Температура охлаждающей воды на входе.
            pif (float | None): Альтернативное значение давления (Pressure In Flow / заданное давление проточной части).
        """
        self.pressure_condenser = pressure_condenser
        self.temperature_cooling_water_1 = temperature_cooling_water_1
        self.pif = pif

        self.pressure_flow_path_1: float | None = None

    def calculate_pressure(self) -> float | None:
        """
        Определяет итоговое давление на основе жестко заданных приоритетов.

        Логика приоритетов:
        1. Высший приоритет: Если `pressure_condenser` задан и больше нуля, 
           используется именно он.
        2. Альтернативный приоритет: Если основные параметры отсутствуют 
           (`pressure_condenser` и температура воды равны None), но задан `pif` > 0, 
           используется значение `pif`.
        3. Если ни одно условие не выполнено, возвращается None.

        Returns:
            float | None: Выбранное значение давления (pressure_flow_path_1) 
                или None, если данные для прямого назначения отсутствуют.
        """
        # Условие 1: Явно заданное давление конденсатора имеет наивысший приоритет
        if self.pressure_condenser is not None and self.pressure_condenser > 0:
            self.pressure_flow_path_1 = self.pressure_condenser
            return self.pressure_flow_path_1

        # Условие 2: Использование альтернативного давления (PIF) при отсутствии основных данных
        if (self.pressure_condenser is None and
                self.temperature_cooling_water_1 is None and
                self.pif is not None and self.pif > 0):
            self.pressure_flow_path_1 = self.pif
            return self.pressure_flow_path_1

        # Данных для исключительного переопределения нет, требуется стандартный расчет
        return None