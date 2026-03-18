import logging
from uniconv import UnitConverter

logger = logging.getLogger(__name__)

# Создаем глобальный инстанс конвертера
converter = UnitConverter()

# Проверяем, есть ли уже энтальпия в конвертере. Если нет - добавляем сами!
try:
    converter.get_available_units("enthalpy")
except Exception:
    logger.info("Добавляем кастомный параметр 'enthalpy' в конвертер...")
    
    converter.add_parameter(
        parameter_type="enthalpy",
        parameter_name="Энтальпия",           # <-- ВОТ ЭТОЙ СТРОКИ НЕ ХВАТАЛО
        base_unit_symbol="кДж/кг",
        base_unit_name="Килоджоуль на килограмм"
    )
    
    # 1 ккал = 4.1868 кДж
    converter.add_unit(
        parameter_type="enthalpy",
        unit_symbol="ккал/кг",
        unit_name="Килокалория на килограмм",
        to_base=4.1868,
        from_base=1/4.1868
    )

    # 1 МДж = 1000 кДж
    converter.add_unit(
        parameter_type="enthalpy",
        unit_symbol="МДж/кг",
        unit_name="Мегаджоуль на килограмм",
        to_base=1000.0,
        from_base=0.001
    )