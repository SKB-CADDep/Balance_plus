from typing import Optional, List, Dict, Any
from app.models.condenser import Condenser


def validate_condenser_for_method(condenser: Condenser, method: str) -> None:
    """
    BR-02: Валидация наличия обязательных констант для выбранной методики.
    Генерирует ValueError если данные некорректны.
    """
    errors = []

    # Геометрия, которая обязательна для обеих методик, уже закрыта nullable=False
    # на уровне базы данных. Здесь проверяем специфику:
    if method == "berman":
        if condenser.aircooler_count is None:
            errors.append(
                "Для методики Бермана обязательно наличие числа трубок воздухоохладителя (aircooler_count).")

    if method == "metro-vickers":
        # Метро-Виккерс использует aircooler_count в адаптере
        if condenser.aircooler_count is None:
            errors.append(
                "Для методики Метро-Виккерса обязательно наличие числа трубок воздухоохладителя (aircooler_count).")

    if errors:
        raise ValueError(f"Ошибка валидации БД (BR-02): {', '.join(errors)}")


def validate_water_flow_limits(
    w_main: float,
    w_builtin: float,
    limits: Optional[Dict[str, Any]]
) -> List[str]:
    """
    BR-06 / BR-07: Валидация расходов охлаждающей воды для конкретной комбинации (цикла).
    Возвращает список сообщений-предупреждений.
    """
    warnings = []
    if not limits:
        return warnings

    main_limits = limits.get("main_bundle", {})
    builtin_limits = limits.get("builtin_bundle", {})

    # BR-07: Если работает только один пучок
    if w_main > 0 and w_builtin <= 0:
        if main_limits:
            if "min" in main_limits and w_main < main_limits["min"]:
                warnings.append(
                    f"Расход ОП ({w_main}) ниже минимума ({main_limits['min']}) для режима одного пучка (BR-07).")
            if "max" in main_limits and w_main > main_limits["max"]:
                warnings.append(
                    f"Расход ОП ({w_main}) выше максимума ({main_limits['max']}) для режима одного пучка (BR-07).")

    elif w_builtin > 0 and w_main <= 0:
        if builtin_limits:
            if "min" in builtin_limits and w_builtin < builtin_limits["min"]:
                warnings.append(
                    f"Расход ВП ({w_builtin}) ниже минимума ({builtin_limits['min']}) для режима одного пучка (BR-07).")
            if "max" in builtin_limits and w_builtin > builtin_limits["max"]:
                warnings.append(
                    f"Расход ВП ({w_builtin}) выше максимума ({builtin_limits['max']}) для режима одного пучка (BR-07).")

    # BR-06: Оба пучка работают
    elif w_main > 0 and w_builtin > 0:
        if main_limits:
            if "min" in main_limits and w_main < main_limits["min"]:
                warnings.append(
                    f"Расход ОП ({w_main}) ниже минимума ({main_limits['min']}) (BR-06).")
            if "max" in main_limits and w_main > main_limits["max"]:
                warnings.append(
                    f"Расход ОП ({w_main}) выше максимума ({main_limits['max']}) (BR-06).")

        if builtin_limits:
            if "min" in builtin_limits and w_builtin < builtin_limits["min"]:
                warnings.append(
                    f"Расход ВП ({w_builtin}) ниже минимума ({builtin_limits['min']}) (BR-06).")
            if "max" in builtin_limits and w_builtin > builtin_limits["max"]:
                warnings.append(
                    f"Расход ВП ({w_builtin}) выше максимума ({builtin_limits['max']}) (BR-06).")

    return warnings
