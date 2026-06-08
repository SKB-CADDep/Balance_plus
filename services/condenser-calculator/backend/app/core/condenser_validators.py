"""
Модуль валидации бизнес-правил (Business Rules - BR).

Содержит набор функций для проверки физической и логической корректности 
входных данных (геометрии оборудования, расходов охлаждающей воды, 
температурных диапазонов). Отделяет правила предметной области от 
математического ядра. Валидаторы могут либо прерывать расчет (выбрасывая 
исключения), либо генерировать предупреждения (warnings), которые 
возвращаются пользователю вместе со сгенерированными матрицами.
"""

import logging
from typing import Optional, List, Dict, Any
from app.models.condenser import Condenser
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

def validate_condenser_for_method(condenser: Condenser, method: str) -> None:
    """
    Проверяет наличие обязательных параметров аппарата для выбранной методики (BR-02).

    Базовые геометрические атрибуты (например, длина трубок) защищены от Null 
    на уровне схемы БД. Однако специфичные параметры (такие как число трубок 
    воздухоохладителя) могут отсутствовать в паспорте. Этот метод проверяет их наличие 
    до запуска математики, чтобы избежать падения ядра.

    Args:
        condenser (Condenser): ORM-объект конденсатора с загруженными свойствами.
        method (str): Выбранная методика расчета ('berman' или 'metro-vickers').

    Raises:
        ValidationError: Если отсутствуют критически важные данные для расчета.
    """
    errors = []

    # Геометрия, которая обязательна для обеих методик, уже закрыта nullable=False
    # на уровне базы данных. Здесь проверяем специфику:
    if method == "berman":
        if condenser.aircooler_count is None:
            errors.append(
                "Для методики Бермана обязательно наличие числа трубок воздухоохладителя (aircooler_count).")

    if method == "metro-vickers":
        # Метро-Виккерс использует aircooler_count в адаптере (расчет коэффициента Kf)
        if condenser.aircooler_count is None:
            errors.append(
                "Для методики Метро-Виккерса обязательно наличие числа трубок воздухоохладителя (aircooler_count).")

    if errors:
        raise ValidationError(
            message="Ошибка валидации БД (BR-02)",
            details=", ".join(errors)
        )


def _check_flow_limit(value: float, limits: dict, bundle_type: str, rule: str) -> List[str]:
    """
    Вспомогательный метод для проверки выхода расхода воды за допустимые границы.

    Args:
        value (float): Текущее значение расхода воды.
        limits (dict): Словарь с ключами 'min' и 'max' (могут быть None).
        bundle_type (str): Текстовое обозначение пучка (например, "ОП" или "ВП") для логов.
        rule (str): Ссылка на бизнес-правило (для формирования текста предупреждения).

    Returns:
        List[str]: Список с текстом предупреждения (пустой список, если нарушений нет).
    """
    warnings = []
    if not limits:
        return warnings

    # Безопасно достаем значения (если ключа нет или там null, получим None)
    min_limit = limits.get("min")
    max_limit = limits.get("max")

    # Явно проверяем, что лимит существует и не равен None, прежде чем сравнивать математически
    if min_limit is not None and value < min_limit:
        warnings.append(
            f"Расход {bundle_type} ({value}) ниже минимума ({min_limit}) ({rule})."
        )
        
    if max_limit is not None and value > max_limit:
        warnings.append(
            f"Расход {bundle_type} ({value}) выше максимума ({max_limit}) ({rule})."
        )
        
    return warnings


def validate_water_flow_limits(
    w_main: float,
    w_builtin: float,
    limits: Optional[Dict[str, Any]]
) -> List[str]:
    """
    Проверяет расходы охлаждающей воды на соответствие паспортным лимитам (BR-06 / BR-07).

    Генерирует некритичные предупреждения (warnings), если расходы выходят за 
    разрешенные заводом-изготовителем пределы. Учитывает режимы работы как с 
    одним пучком (BR-07), так и с двумя активными пучками (BR-06).

    Args:
        w_main (float): Текущий расход основной охлаждающей воды в цикле расчета.
        w_builtin (float): Текущий расход воды во встроенном пучке.
        limits (Optional[Dict[str, Any]]): Паспортные лимиты (из БД).

    Returns:
        List[str]: Список сгенерированных предупреждений.
    """
    warnings = []
    if not limits:
        return warnings

    if w_main == 0 and w_builtin == 0:
        warnings.append(
            "Оба расхода воды равны нулю — проверьте входные данные.")
        return warnings
    
    # Адаптация для унаследованных данных (Legacy Data): 
    # В исторических записях БД лимиты могут храниться как плоский массив [min, max], 
    # а не как структурированный словарь пучков.
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
    Проверяет температуры охлаждающей воды на применимость к методике (BR-10).

    Каждая расчетная стратегия валидна только в определенном диапазоне:
    - Метод Бермана: от 0°С до 45°С.
    - Метод Метро-Виккерса: от 45°С до 150°С.
    При выходе за эти границы формулы теряют точность (экстраполяция).

    Args:
        method (str): Название методики расчета.
        t1_values (List[float]): Массив температур на входе, запрошенных пользователем.

    Returns:
        List[str]: Список предупреждений о выходе за границы достоверности.
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