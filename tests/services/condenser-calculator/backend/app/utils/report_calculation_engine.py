import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import CubicSpline
from app.utils.calculation_engine import k_interpolation_data


def power_law_model(v, a, b, c):
    return a * np.power(v, b) + c

def plot_hybrid_extrapolation():
    speeds = np.array(k_interpolation_data["speed_points"])
    temperatures = np.array(k_interpolation_data["temperature_points"])
    k_values_matrix = np.array(k_interpolation_data["k_values_matrix"])
    new_speeds = np.arange(0, 10.01, 0.2)

    print("Применение гибридной модели с ручной коррекцией от 0 до 0.4 м/с...")
    
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(15, 10))

    for i, temp in enumerate(temperatures):
        k_values_for_temp = k_values_matrix[:, i]
        
        initial_mask = new_speeds < speeds[0]  
        known_mask = (new_speeds >= speeds[0]) & (new_speeds <= speeds.max()) 
        extrapolation_mask = new_speeds > speeds.max() 

        initial_part_speeds = new_speeds[initial_mask]
        first_k_point = k_values_for_temp[0]
        first_speed_point = speeds[0]
        slope = first_k_point / first_speed_point
        k_initial_part = slope * initial_part_speeds

        spline_interpolator = CubicSpline(speeds, k_values_for_temp)
        known_part_speeds = new_speeds[known_mask]
        k_known_part = spline_interpolator(known_part_speeds)

        extrapolation_part_speeds = new_speeds[extrapolation_mask]
        
        num_points_for_fit = 7
        fit_speeds = speeds[-num_points_for_fit:]
        fit_k_values = k_values_for_temp[-num_points_for_fit:]
        
        try:
            initial_guess = [2000, 0.8, 500]
            bounds = ([0, 0.1, -np.inf], [np.inf, 1.5, np.inf])
            params, _ = curve_fit(power_law_model, fit_speeds, fit_k_values, p0=initial_guess, bounds=bounds)
            
            k_extrapolated_part = power_law_model(extrapolation_part_speeds, *params)

            full_k_curve = np.concatenate([k_initial_part, k_known_part, k_extrapolated_part])
            
            ax.plot(new_speeds, full_k_curve, linestyle='-', linewidth=2.0, label=f'{temp} °C')
            ax.scatter(speeds, k_values_for_temp, s=20, zorder=5)

        except RuntimeError:
            print(f"Не удалось аппроксимировать данные для экстраполяции при {temp}°C. Пропускаем.")

    ax.set_title('Зависимость K от скорости', fontsize=18, pad=20)
    ax.set_xlabel('Скорость воды, м/с', fontsize=14)
    ax.set_ylabel('Коэффициент теплопередачи, Вт/(м²·К)', fontsize=14)

    ax.set_xticks(np.arange(0, 10.1, 0.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(bottom=0)

    legend = ax.legend(title='Температура воды, °C', fontsize=11, loc='upper left')
    plt.setp(legend.get_title(), fontsize='12')

    ax.grid(True, which='both', linestyle='--', linewidth=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_hybrid_extrapolation()