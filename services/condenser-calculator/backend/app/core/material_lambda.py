import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.core.exceptions import MaterialPropertyError
from app.utils.table_models import Table1D

logger = logging.getLogger(__name__)

@dataclass
class MaterialLambdaInterpolator:
    """
    Контейнер, хранящий инициализированный объект Table1D и метаданные
    материала для предотвращения повторных аллокаций памяти и быстрых проверок.
    """
    table: Table1D
    min_t: float
    max_t: float
    material_name: str


def build_lambda_interpolator(material:Any) -> MaterialLambdaInterpolator:
    """
    Создает и кэширует интерполятор Table1D для зависимости теплопроводности.
    Должен вызываться один раз перед циклом расчетов.
    """
    if isinstance(material, dict):
        points = material.get("thermal_conductivity_points", [])
        material_name = material.get("name", "Unknown")
    else:
        points = getattr(material, "thermal_conductivity_points", [])
        material_name = getattr(material, "name", "Unknown")

    if not points or len(points) < 2:
        msg = f"Для материала '{material_name}' требуется минимум 2 точки теплопроводности."
        logger.error(msg, extra={"material_name": material_name})
        raise MaterialPropertyError(msg)

    x_vals, y_vals = [], []
    for p in points:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            x_vals.append(float(p[0]))
            y_vals.append(float(p[1]))
        elif isinstance(p, dict):
            x_vals.append(float(p.get("temperature", 0)))
            y_vals.append(float(p.get("value", 0)))
        else:
            x_vals.append(float(getattr(p, "temperature", 0)))
            y_vals.append(float(getattr(p, "value", 0)))

    x = np.array(x_vals, dtype=np.float64)
    y = np.array(y_vals, dtype=np.float64)

    return MaterialLambdaInterpolator(
        table=Table1D(x, y),
        min_t=float(np.min(x)),
        max_t=float(np.max(x)),
        material_name=material_name
    )


def get_lambda(interp: MaterialLambdaInterpolator, t_avg: float) -> float:
    """
    Возвращает коэффициент теплопроводности λ при заданной температуре t_avg.
    Экстраполяция запрещена!
    """
    if not (interp.min_t <= t_avg <= interp.max_t):
        msg = (
            f"Температура {t_avg}°C вне диапазона таблицы λ(T) "
            f"для материала '{interp.material_name}': [{interp.min_t}; {interp.max_t}]"
        )
        logger.error(
            msg,
            extra={
                "material_name": interp.material_name,
                "t_avg": t_avg,
                "min_t": interp.min_t,
                "max_t": interp.max_t
            }
        )
        raise MaterialPropertyError(msg)

    try:
        result = interp.table(t_avg)
    except TypeError:
        if hasattr(interp.table, 'evaluate'):
            result = interp.table.evaluate(t_avg)
        elif hasattr(interp.table, 'get_value'):
            result = interp.table.get_value(t_avg)
        else:
            raise NotImplementedError("Класс Table1D не поддерживает стандартный вызов.")

    return float(result)
