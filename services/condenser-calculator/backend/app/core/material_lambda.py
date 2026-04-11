import numpy as np
from app.utils.table_models import Table1D

def build_lambda_interpolator(material) -> Table1D:
    """
    Создает интерполятор Table1D для зависимости теплопроводности (λ) от температуры.
    
    :param material: Объект материала (ORM-модель или Pydantic-схема)
    :return: Объект Table1D
    """
    points = getattr(material, "thermal_conductivity_points", None)
    material_name = getattr(material, "name", "Unknown")

    if not points or len(points) < 2:
        raise ValueError(
            f"Для материала '{material_name}' требуется минимум 2 точки теплопроводности."
        )

    try:
        x_vals = [float(p.temperature) for p in points]
        y_vals = [float(p.value) for p in points]
    except AttributeError:
        x_vals = [float(p["temperature"]) for p in points]
        y_vals = [float(p["value"]) for p in points]

    x = np.array(x_vals, dtype=np.float64)
    y = np.array(y_vals, dtype=np.float64)

    return Table1D(x, y)


def get_lambda(material, t_avg: float) -> float:
    """
    Возвращает коэффициент теплопроводности λ при заданной температуре t_avg.
    Экстраполяция запрещена! Если t_avg выходит за пределы известных точек,
    выбрасывается исключение ValueError.
    
    :param material: Объект материала
    :param t_avg: Средняя температура материала/воды (°C)
    :return: Коэффициент теплопроводности λ
    """
    points = getattr(material, "thermal_conductivity_points", None)
    material_name = getattr(material, "name", "Unknown")

    if not points or len(points) < 2:
        raise ValueError(
            f"Недостаточно данных теплопроводности для материала '{material_name}'."
        )

    try:
        temps = [float(p.temperature) for p in points]
    except AttributeError:
        temps = [float(p["temperature"]) for p in points]

    min_t = min(temps)
    max_t = max(temps)

    if not (min_t <= t_avg <= max_t):
        raise ValueError(
            f"Температура {t_avg}°C вне диапазона таблицы λ(T) для материала '{material_name}': "
            f"[{min_t}; {max_t}]"
        )

    interpolator = build_lambda_interpolator(material)

    try:
        result = interpolator(t_avg)
    except TypeError:
        if hasattr(interpolator, 'evaluate'):
            result = interpolator.evaluate(t_avg)
        elif hasattr(interpolator, 'get_value'):
            result = interpolator.get_value(t_avg)
        else:
            raise NotImplementedError("Класс Table1D не поддерживает стандартный вызов.")

    return float(result)