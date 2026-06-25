"""
Скрипт визуализации и валидации гибридной математической модели теплопередачи.

Этот модуль генерирует графики (matplotlib), демонстрирующие, как расчетное ядро
(calculation_engine) обрабатывает значения коэффициента теплопередачи (K) 
на границах и за пределами известных табличных данных (ГОСТ).
Используется для визуального контроля отсутствия "выбросов" и математических артефактов.
"""

from _common import setup_path

setup_path()

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import curve_fit

from app.utils.calculation_engine import k_interpolation_data


def power_law_model(v: float | np.ndarray, a: float, b: float, c: float) -> float | np.ndarray:
    """
    Математическая модель степенной зависимости для физичной экстраполяции.

    [ENGINEERING CONTEXT]
    Почему выбрана форма `a * v^b + c`: 
    В теории конвективного теплообмена (например, по уравнению Диттуса-Белтера) 
    критерий Нуссельта (а значит и коэффициент теплоотдачи K) для турбулентного потока 
    в трубе пропорционален числу Рейнольдса в степени ~0.8 (Re^0.8). Так как Re 
    линейно зависит от скорости воды (v), данная функция физически достоверно 
    описывает замедляющийся рост K при высоких скоростях.

    Args:
        v (float | np.ndarray): Скорость охлаждающей воды в м/с.
        a (float): Масштабирующий коэффициент.
        b (float): Показатель степени (ожидается около 0.8).
        c (float): Смещение базовой линии.

    Returns:
        float | np.ndarray: Расчетное значение коэффициента теплопередачи.
    """
    return a * np.power(v, b) + c


def plot_hybrid_extrapolation() -> None:
    """
    Строит графики коэффициента теплопередачи (K) в зависимости от скорости воды (v).

    Реализует "гибридную" логику склейки трех математических моделей:
    1. Линейное падение к нулю (при v < минимальной табличной).
    2. Кубический сплайн (для табличных значений).
    3. Степенная регрессия (для v > максимальной табличной).
    """
    speeds = np.array(k_interpolation_data["speed_points"])
    temperatures = np.array(k_interpolation_data["temperature_points"])
    k_values_matrix = np.array(k_interpolation_data["k_values_matrix"])
    new_speeds = np.arange(0, 10.01, 0.2)

    print("Применение гибридной модели с ручной коррекцией от 0 до 0.4 м/с...")

    plt.style.use("ggplot")
    _fig, ax = plt.subplots(figsize=(15, 10))

    for i, temp in enumerate(temperatures):
        k_values_for_temp = k_values_matrix[:, i]

        # Разделение массива запрошенных скоростей на 3 смысловые зоны
        initial_mask = new_speeds < speeds[0]
        known_mask = (new_speeds >= speeds[0]) & (new_speeds <= speeds.max())
        extrapolation_mask = new_speeds > speeds.max()

        # [ENGINEERING CONTEXT]
        # Зона 1: Экстраполяция к нулю.
        # Запрет на экстраполяцию сплайном вниз: Кубические сплайны при попытке уйти в 0
        # часто дают физически невозможные отрицательные значения коэффициента теплоотдачи.
        # Поэтому мы жестко задаем линейное падение в ноль, фиксируя наклон по первой известной точке.
        initial_part_speeds = new_speeds[initial_mask]
        first_k_point = k_values_for_temp[0]
        first_speed_point = speeds[0]
        slope = first_k_point / first_speed_point
        k_initial_part = slope * initial_part_speeds

        # Зона 2: Внутритабличная интерполяция (CubicSpline гарантирует гладкость производных)
        spline_interpolator = CubicSpline(speeds, k_values_for_temp)
        known_part_speeds = new_speeds[known_mask]
        k_known_part = spline_interpolator(known_part_speeds)

        # [ENGINEERING CONTEXT]
        # Зона 3: Экстраполяция сверхвысоких скоростей.
        # Кубические полиномы за пределами интерполяционной сетки стремятся к бесконечности.
        # Для защиты расчетного ядра, мы берем последние `num_points_for_fit` (7) точек кривой 
        # и "натягиваем" на них степенную функцию через метод наименьших квадратов (curve_fit).
        extrapolation_part_speeds = new_speeds[extrapolation_mask]

        num_points_for_fit = 7
        fit_speeds = speeds[-num_points_for_fit:]
        fit_k_values = k_values_for_temp[-num_points_for_fit:]

        try:
            # [ENGINEERING CONTEXT]
            # initial_guess[1] = 0.8 выбран именно из-за физики турбулентного течения.
            # bounds = ([...], [..., 1.5, ...]) запрещает алгоритму оптимизации находить решения,
            # где показатель степени больше 1.5 (что привело бы к нереалистичному взлету K).
            initial_guess = [2000, 0.8, 500]
            bounds = ([0, 0.1, -np.inf], [np.inf, 1.5, np.inf])
            params, _ = curve_fit(power_law_model, fit_speeds, fit_k_values, p0=initial_guess, bounds=bounds)

            k_extrapolated_part = power_law_model(extrapolation_part_speeds, *params)

            # Склейка трех зон в единую физичную кривую
            full_k_curve = np.concatenate([k_initial_part, k_known_part, k_extrapolated_part])

            ax.plot(new_speeds, full_k_curve, linestyle="-", linewidth=2.0, label=f"{temp} °C")
            ax.scatter(speeds, k_values_for_temp, s=20, zorder=5)

        except RuntimeError:
            print(f"Не удалось аппроксимировать данные для экстраполяции при {temp}°C. Пропускаем.")

    # Настройка визуального отображения графика
    ax.set_title("Зависимость K от скорости", fontsize=18, pad=20)
    ax.set_xlabel("Скорость воды, м/с", fontsize=14)
    ax.set_ylabel("Коэффициент теплопередачи, Вт/(м²·К)", fontsize=14)

    ax.set_xticks(np.arange(0, 10.1, 0.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(bottom=0)

    legend = ax.legend(title="Температура воды, °C", fontsize=11, loc="upper left")
    plt.setp(legend.get_title(), fontsize="12")

    ax.grid(True, which="both", linestyle="--", linewidth=0.7)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_hybrid_extrapolation()
    