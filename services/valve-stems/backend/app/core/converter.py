"""
Модуль инициализации и настройки конвертера физических величин.

Использует библиотеку uniconv для приведения входных данных пользователя
(ккал/кг, МДж/кг) к единой системе СИ (кДж/кг), которая используется
математическим ядром при расчетах.
"""

import logging

from uniconv import UnitConverter

logger = logging.getLogger(__name__)

# Глобальный инстанс конвертера для использования во всем приложении.
# Строгая типизация добавлена для корректной работы MyPy и автодополнения в IDE.
converter: UnitConverter = UnitConverter()

# Инициализация кастомных физических величин.
# Проверяем наличие параметра 'enthalpy' (энтальпия). Если он отсутствует
# в базовой конфигурации uniconv, регистрируем его динамически.
try:
    converter.get_available_units("enthalpy")
except Exception as e:
    # WARNING (Технический долг):
    # Перехват базового Exception (broad exception) является антипаттерном.
    # В будущем желательно заменить на конкретное исключение из библиотеки uniconv,
    # чтобы не пропустить реальные сбои в логике.
    logger.info("Инициализация кастомного параметра 'enthalpy' в конвертере.")
    
    converter.add_parameter(
        parameter_type="enthalpy",
        parameter_name="Энтальпия",
        base_unit_symbol="кДж/кг",
        base_unit_name="Килоджоуль на килограмм"
    )
    
    # Регистрация коэффициентов перевода: 1 ккал = 4.1868 кДж
    converter.add_unit(
        parameter_type="enthalpy",
        unit_symbol="ккал/кг",
        unit_name="Килокалория на килограмм",
        to_base=4.1868,
        from_base=1 / 4.1868
    )

    # Регистрация коэффициентов перевода: 1 МДж = 1000 кДж
    converter.add_unit(
        parameter_type="enthalpy",
        unit_symbol="МДж/кг",
        unit_name="Мегаджоуль на килограмм",
        to_base=1000.0,
        from_base=0.001
    )
    