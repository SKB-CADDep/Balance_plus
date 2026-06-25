"""
Инфраструктура для расчета коэффициента теплопроводности материалов (λ).

Модуль отвечает за создание оптимизированных математических моделей 
(интерполяторов) на основе паспортных данных материала трубок. 
Обеспечивает строгое соблюдение физических ограничений (запрет 
на экстраполяцию свойств материала за границы известных экспериментальных данных).
"""

import logging
import numpy as np
from dataclasses import dataclass
from app.utils.table_models import Table1D
from app.core.exceptions import MaterialPropertyError

logger = logging.getLogger(__name__)

@dataclass
class MaterialLambdaInterpolator:
    """
    Кэширующий контейнер-обертка для одномерного интерполятора теплопроводности.

    Хранит инициализированный объект `Table1D` вместе с предвычисленными 
    границами (min_t, max_t) и названием материала. Передается в вычислительное 
    ядро для предотвращения повторных аллокаций памяти и обеспечения 
    очень быстрых проверок границ (O(1)) внутри тяжелых итерационных циклов.
    """
    table: Table1D
    min_t: float
    max_t: float
    material_name: str


def build_lambda_interpolator(material) -> MaterialLambdaInterpolator:
    """
    Создает объект интерполятора на основе "сырых" данных о материале.

    Метод реализует шаблон проектирования "Адаптер" на уровне данных: 
    он умеет извлекать точки графика λ(T) независимо от того, в каком виде 
    пришел объект `material` (Pydantic-схема, словарь JSON или объект БД SQLAlchemy).
    Должен вызываться один раз перед началом основного цикла расчетов.

    Args:
        material (Any): Объект или словарь с данными материала. Ожидается 
            наличие свойства/ключа `thermal_conductivity_points`.

    Returns:
        MaterialLambdaInterpolator: Готовый к использованию контейнер интерполятора.

    Raises:
        MaterialPropertyError: Если у материала отсутствует таблица теплопроводности 
            или количество точек в ней меньше двух (невозможно построить график).
    """
    # Полиморфизм: извлекаем данные независимо от типа входящего объекта
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

    # Нормализация структуры точек: поддержка массивов, словарей и объектов
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
        min_t=float(np.min(x)),  # Кэшируем минимальную температуру
        max_t=float(np.max(x)),  # Кэшируем максимальную температуру
        material_name=material_name
    )


def get_lambda(interp: MaterialLambdaInterpolator, t_avg: float) -> float:
    """
    Вычисляет значение коэффициента теплопроводности (λ) для заданной температуры.

    Бизнес-правило (Физика): Экстраполяция физических свойств сплавов ЗАПРЕЩЕНА.
    Если расчетная температура стенки трубы выходит за пределы экспериментальной 
    таблицы (например, таблица до 100°C, а расчет требует 120°C), ядро 
    обязано прервать расчет и выбросить ошибку, так как полиномиальная экстраполяция 
    может выдать физически некорректное значение теплопроводности.

    Args:
        interp (MaterialLambdaInterpolator): Подготовленный контейнер интерполятора.
        t_avg (float): Средняя температура стенки трубки (в °C).

    Returns:
        float: Значение теплопроводности λ.

    Raises:
        MaterialPropertyError: Если запрошенная температура выходит за границы `[min_t, max_t]`.
        NotImplementedError: Если интерфейс переданного объекта `Table1D` не поддерживается.
    """
    # Строгая проверка границ O(1)
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

    # Безопасное извлечение значения с поддержкой различных версий интерфейса Table1D
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