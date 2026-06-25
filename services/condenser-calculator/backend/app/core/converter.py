import logging

from app.utils.uniconv import UnitConverter

logger = logging.getLogger(__name__)

converter = UnitConverter()

# Проверяем параметр энтальпии
try:
    converter.get_available_units("enthalpy")
except Exception:
    logger.info("Добавляем параметр 'enthalpy' в конвертер")

    converter.add_parameter(
        parameter_type="enthalpy",
        parameter_name="Энтальпия",
        base_unit_symbol="кДж/кг",
        base_unit_name="Килоджоуль на килограмм",
    )

    # 1 ккал = 4.1868 кДж
    converter.add_unit(
        parameter_type="enthalpy",
        unit_symbol="ккал/кг",
        unit_name="Килокалория на килограмм",
        to_base=4.1868,
        from_base=1 / 4.1868,
    )
