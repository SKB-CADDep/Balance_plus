"""
Модуль валидации бизнес-правил (Business Rules - BR).

Содержит набор функций для проверки физической и логической корректности 
входных данных (геометрии оборудования, расходов охлаждающей воды, 
температурных диапазонов). Отделяет правила предметной области от 
математического ядра. Валидаторы могут либо прерывать расчет (выбрасывая 
исключения), либо генерировать предупреждения (warnings), которые 
возвращаются пользователю вместе со сгенерированными матрицами.
"""

from typing import List, Dict, Any, Optional

from app.core.exceptions import ValidationError
from app.models.condenser import Condenser


def validate_condenser_for_method(condenser: Condenser, method: str) -> None:
    """
    Проверяет наличие обязательных геометрических параметров аппарата (BR-02).
    """
    missing_fields = []
    
    if not condenser.diameter_internal:
        missing_fields.append("Внутренний диаметр труб")
    if not condenser.wall_thickness:
        missing_fields.append("Толщина стенки труб")
    if not condenser.main_length:
        missing_fields.append("Длина трубок основного пучка")
    if not condenser.main_count:
        missing_fields.append("Количество трубок основного пучка")
    if condenser.aircooler_count is None:
        missing_fields.append("Количество трубок воздухоохладителя")
        
    if missing_fields:
        raise ValidationError(
            message="Недостаточно данных об оборудовании для проведения расчета.",
            details=f"Отсутствуют параметры: {', '.join(missing_fields)}"
        )


def _check_flow_limit(value: float, limits: dict, bundle_type: str, rule: str) -> List[str]:
    """
    Вспомогательная функция проверки конкретного значения расхода на попадание в лимиты.
    """
    warnings = []
    
    min_limit = limits.get("min")
    max_limit = limits.get("max")
    
    if min_limit is not None and value < min_limit:
        warnings.append(f"Расход {bundle_type} ({value}) ниже минимума ({min_limit}) ({rule}).")
    
    if max_limit is not None and value > max_limit:
        warnings.append(f"Расход {bundle_type} ({value}) выше максимума ({max_limit}) ({rule}).")
        
    return warnings


def validate_water_flow_limits(w_main: float, w_builtin: float, limits: Optional[Dict[str, Any]]) -> List[str]:
    """
    Проверяет расходы охлаждающей воды на соответствие паспортным лимитам (BR-06 / BR-07).
    """
    warnings = []
    if not limits:
        return warnings

    if w_main == 0 and w_builtin == 0:
        warnings.append("Оба расхода воды равны нулю — проверьте входные данные.")
        return warnings
    
    # Адаптация для унаследованных данных (Legacy Data): 
    if isinstance(limits, list) and len(limits) == 2:
        limits = {
            "main_bundle": {"min": limits[0], "max": limits[1]},
            "builtin_bundle": None
        }

    if not isinstance(limits, dict):
        return []

    main_limits = limits.get("main_bundle") or {}
    builtin_limits = limits.get("builtin_bundle") or {}

    # BR-07: Если работает только один пучок
    if w_main > 0 and w_builtin <= 0:
        warnings.extend(_check_flow_limit(w_main, main_limits, "ОП", "режима одного пучка (BR-07)"))

    elif w_builtin > 0 and w_main <= 0:
        warnings.extend(_check_flow_limit(w_builtin, builtin_limits, "ВП", "режима одного пучка (BR-07)"))

    # BR-06: Оба пучка работают
    elif w_main > 0 and w_builtin > 0:
        warnings.extend(_check_flow_limit(w_main, main_limits, "ОП", "BR-06"))
        warnings.extend(_check_flow_limit(w_builtin, builtin_limits, "ВП", "BR-06"))

    return warnings


def validate_temperature_ranges(method: str, t1_values: List[float]) -> List[str]:
    """
    Проверяет температуры охлаждающей воды на применимость к методике (BR-10).
    """
    warnings = []
    
    if not t1_values:
        return warnings
    
    min_t = min(t1_values)
    max_t = max(t1_values)

    if method == "berman":
        if min_t < 0 or max_t > 45:
            warnings.append(
                f"Температуры выходят за диапазон применимости Бермана (0...45°C). "
                f"Min: {min_t}, Max: {max_t}"
            )
    elif method == "metro-vickers":
        if min_t < 45 or max_t > 150:
            warnings.append(
                f"Температуры выходят за диапазон применимости Метро-Виккерса (45...150°C). "
                f"Min: {min_t}, Max: {max_t}"
            )
            
    return warnings
    