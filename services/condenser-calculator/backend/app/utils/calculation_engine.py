import math
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import seuif97
from uniconv import UnitConverter

coefficient_B_const = 1.0

k_interpolation_data = {
    "temperature_points": [5, 15, 27, 38, 50, 70, 95, 120, 150],  # Средняя температура tср [°C]
    "speed_points": [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 1.9, 2.0, 2.1, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6], # Скорость воды Cов [м/с]
    "k_values_matrix": [
        [800, 1050, 1260, 1430, 1540, 1670, 1770, 1870, 1930],
        [1260, 1510, 1720, 1890, 2000, 2170, 2270, 2370, 2430],
        [1670, 1920, 2130, 2300, 2430, 2600, 2700, 2800, 2860],
        [1970, 2220, 2450, 2620, 2750, 2950, 3060, 3160, 3230],
        [2200, 2450, 2680, 2850, 2990, 3190, 3290, 3390, 3490],
        [2410, 2680, 2900, 3080, 3210, 3400, 3520, 3620, 3700],
        [2590, 2840, 3070, 3230, 3380, 3570, 3690, 3790, 3880],
        [2760, 3010, 3230, 3420, 3550, 3730, 3850, 3960, 4040],
        [2830, 3080, 3300, 3490, 3630, 3810, 3930, 4040, 4120],
        [2900, 3150, 3370, 3570, 3700, 3870, 4000, 4110, 4190],
        [2980, 3230, 3440, 3640, 3770, 3950, 4070, 4180, 4250],
        [3040, 3290, 3500, 3690, 3830, 4000, 4120, 4220, 4310],
        [3150, 3400, 3620, 3810, 3940, 4120, 4230, 4350, 4420],
        [3250, 3500, 3710, 3910, 4040, 4220, 4330, 4440, 4540],
        [3340, 3590, 3800, 3990, 4130, 4320, 4420, 4530, 4610],
        [3440, 3690, 3870, 4050, 4180, 4390, 4500, 4600, 4670],
        [3500, 3750, 3930, 4100, 4230, 4460, 4560, 4660, 4730],
        [3560, 3810, 3990, 4160, 4290, 4520, 4620, 4720, 4790],
        [3600, 3850, 4040, 4200, 4340, 4560, 4660, 4760, 4840]
    ]
}

def calculate_pressure(params):
    get_k_from_table_temp = RegularGridInterpolator(
        (k_interpolation_data["speed_points"], k_interpolation_data["temperature_points"]),
        np.array(k_interpolation_data["k_values_matrix"]),
        method="linear",
        bounds_error=False,
        fill_value=None
    )

    get_heat_of_vaporization = lambda temp: (30 - temp) * 0.582 + 580.4
    uc = UnitConverter()

    d_in = params['diameter_inside_of_pipes']
    s_w = params['thickness_pipe_wall']
    L = params['length_cooling_tubes_of_the_main_bundle']
    N_main = params['number_cooling_tubes_of_the_main_bundle']
    N_extra = params['number_cooling_tubes_of_the_built_in_bundle']
    n_passes = params['number_cooling_water_passes_of_the_main_bundle']
    m_cw = params['mass_flow_cooling_water']
    T_cw1 = params['temperature_cooling_water_1']
    lambda_mat = params['thermal_conductivity_cooling_surface_tube_material']
    b = params.get('coefficient_b', 1.0)
    m_flow = params['mass_flow_flow_path_1']
    dryness = params['degree_dryness_flow_path_1']
    N_total = params.get('number_air_cooler_total_pipes', (N_main + N_extra) * 0.15)

    d_out = d_in + 2 * s_w
    area_total = (math.pi * L * N_main * d_out * 1e-6)
    area_air = (math.pi * L * N_total * d_out * 1e-6)

    Kf = 1 - 0.225 * (area_air / area_total) if area_total > 0 else 1.0
    R1 = ((2 * s_w / 1000 * d_out / 1000) /
          ((d_out / 1000 + d_in / 1000) * lambda_mat))

    speed = (m_cw * n_passes) / (900 * math.pi * (N_main + N_extra) * (d_in / 1000) ** 2)
    r_vap = get_heat_of_vaporization(T_cw1)

    dT = (m_flow * r_vap * dryness) / m_cw
    T_cw2 = T_cw1 + dT
    T_avg = (T_cw1 + T_cw2) / 2

    # Итерационный подбор K (теперь без повторного создания интерполятора)
    max_iter, tol = 20, 0.001
    K_temp = get_k_from_table_temp((speed, T_avg)).item()

    for _ in range(max_iter):
        k_new = get_k_from_table_temp((speed, T_avg)).item()
        if abs(k_new - K_temp) < tol:
            K_temp = k_new
            break
        K_temp = k_new

    denom_clean = (1 / (K_temp * 0.85 * coefficient_B_const * Kf)) - 0.087 / 10000 + R1
    K_clean = 1 / denom_clean
    R = (1 / K_clean) * ((1 / b) - 1)
    denom_zag = denom_clean + R
    K_zag = 1 / denom_zag

    delta_T_rel = 1 / (math.e ** ((K_zag * area_total) / (m_cw * 1000)) - 1)
    T_sat = T_cw2 + delta_T_rel * (T_cw2 - T_cw1)

    T_K = uc.convert(T_sat, from_unit="°C", to_unit="K", parameter_type="temperature")
    p_MPa = seuif97.tx2p(T_sat, 1)
    p_kgf = uc.convert(p_MPa, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure")

    res_str = f"| {m_cw:<8.1f} | {T_cw1:<8.1f} | {T_cw2:<8.2f} | {T_sat:<8.2f} | {m_flow:<7.1f} | {p_kgf:<11.4f} |"
    print(res_str)

    return {
        'd_out': d_out, 'area_total': area_total, 'area_air': area_air, 'Kf': Kf, 'R1': R1,
        'speed': speed, 'r_vap': r_vap, 'T_cw2': T_cw2, 'T_avg': T_avg, 'K_temp': K_temp,
        'K_clean': K_clean, 'R': R, 'K_zag': K_zag, 'delta_T_rel': delta_T_rel,
        'T_sat': T_sat, 'p_kgf': p_kgf
    }


def batch_calculate(params_template, varying_params: dict):
    from itertools import product

    keys = list(varying_params.keys())
    values = list(varying_params.values())

    results = []
    for combo in product(*values):
        params = params_template.copy()
        params.update(dict(zip(keys, combo)))
        res = calculate_pressure(params)
        res.update(dict(zip(keys, combo)))
        results.append(res)

    return results