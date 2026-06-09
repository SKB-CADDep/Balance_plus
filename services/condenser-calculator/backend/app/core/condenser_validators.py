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

# (Здесь остается ваша функция _check_flow_limit)


def validate_water_flows(w_main: float, w_builtin: float, limits: Optional[Dict[str, Any]]) -> List[str]:
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
        warnings.append("Оба расхода воды равны нулю — проверьте входные данные.")
        return warnings
    
    # --- ИСПРАВЛЕНИЕ ОШИБКИ (Legacy Data) ---
    # В исторических записях БД лимиты могут храниться как плоский массив [min, max], 
    # а не как структурированный словарь пучков.
    # Мы применяем этот старый лимит ТОЛЬКО к основному пучку (main_bundle).
    # Для встроенного пучка ставим None, чтобы не применять к нему гигантские расходы.
    if isinstance(limits, list) and len(limits) == 2:
        limits = {
            "main_bundle": {"min": limits[0], "max": limits[1]},
            "builtin_bundle": None
        }

    if not isinstance(limits, dict):
        return []

    # Используем 'or {}', чтобы избежать ошибок, если для пучка стоит None
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

    Каждая расчетная стратегия валидна только в определенном диапазоне:
    - Метод Бермана: от 0°С до 45°С.
    - Метод Метро-Виккерса: от 45°С до 150°С.
    При выходе за эти границы формулы теряют точность (экстраполяция).

    Args:
        method (str): Название методики расчета.
        t1_values (List[float]): Массив температур на входе, запрошенных пользователем.

    Returns:
        List[str]: Список сгенерированных предупреждений.
    """
    # (Здесь остается ваша логика проверки температур)