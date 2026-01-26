from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from scipy.interpolate import interp1d, RegularGridInterpolator
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Table1D:
    """
    Представляет 1D таблицу для быстрой интерполяции и экстраполяции.

    При создании объекта выполняются все "дорогие" вычисления:
    1. Данные сортируются и валидируются.
    2. Создается объект для быстрой линейной интерполяции.
    3. Подбирается и сохраняется наилучшая полиномиальная модель для экстраполяции.
    """
    x_cords: np.ndarray
    y_cords: np.ndarray
    max_extrap_degree: int = 3

    # Приватные поля для хранения "дорогих" объектов
    _interp: interp1d = field(init=False, repr=False)
    _extrap_model: np.poly1d = field(init=False, repr=False)
    _best_extrap_degree: int = field(init=False, repr=False)

    def __post_init__(self):
        # Валидация входных данных
        if not isinstance(self.x_cords, np.ndarray) or not isinstance(self.y_cords, np.ndarray):
            raise TypeError("x_cords и y_cords должны быть экземплярами np.ndarray.")
        if self.x_cords.ndim != 1 or self.y_cords.ndim != 1:
            raise ValueError("x_cords и y_cords должны быть 1-мерными массивами.")
        if self.x_cords.size != self.y_cords.size:
            raise ValueError("Размеры x_cords и y_cords должны совпадать.")
        if self.x_cords.size == 0:
            raise ValueError("Массивы координат не могут быть пустыми.")

        # Шаг 1: Подготовка данных и создание интерполятора
        sort_indices = np.argsort(self.x_cords)
        x_sorted = self.x_cords[sort_indices]
        y_sorted = self.y_cords[sort_indices]

        # Проверка на строгое возрастание и отсутствие дубликатов X
        if np.any(np.diff(x_sorted) <= 0):
            raise ValueError(
                "Координаты X должны быть строго возрастающими и не содержать дубликатов после сортировки.")

        object.__setattr__(self, 'x_cords', x_sorted)
        object.__setattr__(self, 'y_cords', y_sorted)

        # Создаем интерполятор один раз
        interp_func = interp1d(x_sorted, y_sorted, kind="linear", bounds_error=False, fill_value=np.nan)
        object.__setattr__(self, '_interp', interp_func)

        # Шаг 2: Подбор и кэширование лучшей модели для экстраполяции
        self._fit_extrapolation_model()

    def _fit_extrapolation_model(self):
        """
        Находит лучшую полиномиальную модель и сохраняет ее в self._extrap_model.
        Вызывается один раз из __post_init__.
        """
        best_model = None
        best_aic = float('inf')
        best_degree = -1
        n = len(self.x_cords)

        logger.info(
            f"[{self.__class__.__name__}] Поиск лучшей модели для экстраполяции (max_degree={self.max_extrap_degree})")

        for degree in range(1, self.max_extrap_degree + 1):
            if degree >= n:
                logger.warning(
                    f"[{self.__class__.__name__}] Степень полинома ({degree}) >= кол-ва точек ({n}). Поиск прерван.")
                break

            coeffs = np.polyfit(self.x_cords, self.y_cords, degree)
            model = np.poly1d(coeffs)

            y_pred = model(self.x_cords)
            rss = np.sum((self.y_cords - y_pred) ** 2)
            k = degree + 1

            aic = n * np.log(rss / n) + 2 * k if rss > 0 else -np.inf
            logger.debug(f"[{self.__class__.__name__}] Степень: {degree}, AIC: {aic:.4f}")

            if aic < best_aic:
                best_aic = aic
                best_model = model
                best_degree = degree

        if best_model is None:
            raise RuntimeError("Не удалось построить модель для экстраполяции.")

        logger.info(
            f"-> [{self.__class__.__name__}] Выбрана модель для экстраполяции: полином степени {best_degree} (AIC={best_aic:.4f})")
        object.__setattr__(self, '_extrap_model', best_model)
        object.__setattr__(self, '_best_extrap_degree', best_degree)

    def __call__(self, target_x: float | np.ndarray) -> float | np.ndarray:
        """
        Выполняет интерполяцию или экстраполяцию для target_x.
        Метод сам решает, какой инструмент использовать.
        Поддерживает как скалярные значения, так и массивы NumPy.
        """
        interpolated_values = self._interp(target_x)

        if np.isscalar(target_x):
            if not np.isnan(interpolated_values):
                return float(interpolated_values)
            else:
                logger.warning(
                    f"-> [{self.__class__.__name__}] Точка X={target_x} вне диапазона. Используется экстраполяция (полином ст. {self._best_extrap_degree}).")
                return float(self._extrap_model(target_x))

        output_values = np.copy(interpolated_values)
        extrapolation_indices = np.isnan(interpolated_values)

        if np.any(extrapolation_indices):
            logger.warning(
                f"-> [{self.__class__.__name__}] {np.sum(extrapolation_indices)} точка(и) вне диапазона. Используется экстраполяция (полином ст. {self._best_extrap_degree}).")
            x_to_extrapolate = np.asarray(target_x)[extrapolation_indices]
            output_values[extrapolation_indices] = self._extrap_model(x_to_extrapolate)

        return output_values


@dataclass(frozen=True)
class Table2D:
    """
    Представляет 2D таблицу для билинейной интерполяции.
    Координаты x и y должны быть 1D массивами, строго возрастающими.
    """
    x_cords: np.ndarray
    y_cords: np.ndarray
    z_values: np.ndarray
    _rgi: RegularGridInterpolator = field(init=False, repr=False)

    def __post_init__(self):
        if not all(isinstance(arr, np.ndarray) for arr in [self.x_cords, self.y_cords, self.z_values]):
            raise TypeError("x_cords, y_cords, и z_values должны быть экземплярами np.ndarray.")
        if self.x_cords.ndim != 1 or self.y_cords.ndim != 1 or self.z_values.ndim != 2:
            raise ValueError("Ожидаем 1-D x, 1-D y и 2-D z")
        if self.z_values.shape != (self.x_cords.size, self.y_cords.size):
            raise ValueError(
                f"Размеры z {self.z_values.shape} не соответствуют ({self.x_cords.size}, {self.y_cords.size})")
        if np.any(np.diff(self.x_cords) <= 0):
            raise ValueError("x_cords должен быть строго возрастающим")
        if np.any(np.diff(self.y_cords) <= 0):
            raise ValueError("y_cords должен быть строго возрастающим")

        rgi_func = RegularGridInterpolator((self.x_cords, self.y_cords), self.z_values,
                                           method="linear", bounds_error=False, fill_value=np.nan)
        object.__setattr__(self, '_rgi', rgi_func)

    def __call__(self, target_x: float | np.ndarray,
                 target_y: float | np.ndarray) -> float | np.ndarray:
        points_x = np.ravel(target_x)
        points_y = np.ravel(target_y)
        points_to_interpolate = np.column_stack((points_x, points_y))
        interpolated_values = self._rgi(points_to_interpolate)
        return interpolated_values.reshape(np.shape(target_x))


def interpolate_trilinear(
        table_low_a: Table2D, a_low: float,
        table_high_a: Table2D, a_high: float,
        target_x: float, target_y: float, target_a: float) -> float:
    """
    Выполняет линейно-билинейную (трилинейную) интерполяцию.
    Сначала выполняется билинейная интерполяция для target_x, target_y
    в table_low_a и table_high_a.
    Затем выполняется линейная интерполяция по target_a между полученными значениями.

    Args:
        table_low_a: Объект Table2D для нижнего значения параметра A.
        a_low: Значение параметра A, соответствующее table_low_a.
        table_high_a: Объект Table2D для верхнего значения параметра A.
        a_high: Значение параметра A, соответствующее table_high_a.
        target_x: Целевое значение X.
        target_y: Целевое значение Y.
        target_a: Целевое значение A.

    Returns:
        Интерполированное значение Z.
    """
    z_at_a_low = table_low_a(target_x, target_y)
    z_at_a_high = table_high_a(target_x, target_y)

    # Преобразование в float, если это скалярные значения в массивах размером 1
    if isinstance(z_at_a_low, np.ndarray) and z_at_a_low.size == 1:
        z_at_a_low = float(z_at_a_low.item())
    if isinstance(z_at_a_high, np.ndarray) and z_at_a_high.size == 1:
        z_at_a_high = float(z_at_a_high.item())

    if np.isnan(z_at_a_low) or np.isnan(z_at_a_high):
        logger.warning(f"Один из промежуточных Z является NaN (Z_low={z_at_a_low}, Z_high={z_at_a_high}). "
                       f"Результат по A также будет NaN.")
        return np.nan

    final_z = np.interp(target_a, [a_low, a_high], [z_at_a_low, z_at_a_high])
    return float(final_z)
