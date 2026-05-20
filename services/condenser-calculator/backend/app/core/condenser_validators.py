import logging
from typing import Optional, List, Dict, Any
from app.models.condenser import Condenser
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

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
        raise ValidationError(
            message="Ошибка валидации БД (BR-02)",
            details=", ".join(errors)
        )


def _check_flow_limit(value: float, limits: dict, bundle_type: str, rule: str) -> List[str]:
    """Вспомогательный метод для проверки лимитов одного пучка."""
    warnings = []
    if not limits:
        return warnings

    if "min" in limits and value < limits["min"]:
        warnings.append(
            f"Расход {bundle_type} ({value}) ниже минимума ({limits['min']}) ({rule}).")
    if "max" in limits and value > limits["max"]:
        warnings.append(
            f"Расход {bundle_type} ({value}) выше максимума ({limits['max']}) ({rule}).")
    return warnings


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

    if w_main == 0 and w_builtin == 0:
        warnings.append(
            "Оба расхода воды равны нулю — проверьте входные данные.")
        return warnings
    
    # ФИКС: Обработка списка [4000, 20000], который реально лежит в вашей базе
    if isinstance(limits, list) and len(limits) == 2:
        limits = {
            "main_bundle": {"min": limits[0], "max": limits[1]},
            "builtin_bundle": {"min": 0, "max": limits[1]}
        }

    if not isinstance(limits, dict):
        return []

    main_limits = limits.get("main_bundle", {})
    builtin_limits = limits.get("builtin_bundle", {})

    # BR-07: Если работает только один пучок
    if w_main > 0 and w_builtin <= 0:
        warnings.extend(_check_flow_limit(w_main, main_limits,
                        "ОП", "режима одного пучка (BR-07)"))

    elif w_builtin > 0 and w_main <= 0:
        warnings.extend(_check_flow_limit(
            w_builtin, builtin_limits, "ВП", "режима одного пучка (BR-07)"))

    # BR-06: Оба пучка работают
    elif w_main > 0 and w_builtin > 0:
        warnings.extend(_check_flow_limit(w_main, main_limits, "ОП", "BR-06"))
        warnings.extend(_check_flow_limit(
            w_builtin, builtin_limits, "ВП", "BR-06"))

    return warnings


def validate_temperature_ranges(method: str, t1_values: List[float]) -> List[str]:
    """
    BR-10: Валидация температурных диапазонов для t1.
    Берман: 0..45
    Метро-Виккерс: 45..150
    """
    warnings = []
    if not t1_values:
        return warnings

    min_t = min(t1_values)
    max_t = max(t1_values)

    if method == "berman":
        if min_t < 0 or max_t > 45:
            warnings.append(
                "t1 содержит значения вне оптимального диапазона 0...45°С (Берман).")
    elif method == "metro-vickers":
        if min_t < 45 or max_t > 150:
            warnings.append(
                "t1 содержит значения вне оптимального диапазона 45...150°С (Метро-Виккерс).")

    return warnings
