"""
Математическое ядро расчета конденсаторов по методике Метро-Виккерс.

В основе метода лежит эмпирическая матрица коэффициентов теплопередачи (k), 
зависящая от скорости воды в трубках и её средней температуры. 
Для получения промежуточных значений используется двумерная (билинейная) интерполяция.

Содержит:
- Инициализацию глобального интерполятора.
- Функцию точечного расчета (calculate_pressure) — Фасад.
- Функцию генерации массивов результатов (batch_calculate).
"""

import math
import numpy as np
import seuif97
from scipy.interpolate import RegularGridInterpolator
from itertools import product

from .uniconv import UnitConverter
from app.utils import Constants as const  # Импортируем базу данных констант

# =====================================================================
# ИНИЦИАЛИЗАЦИЯ ЯДРА (Выполняется 1 раз при импорте модуля)
# =====================================================================

# Оптимизация производительности: Интерполятор и конвертер создаются ОДИН раз.
_INTERPOLATOR = RegularGridInterpolator(
    (const.k_interpolation_data["speed_points"], const.k_interpolation_data["temperature_points"]),
    np.array(const.k_interpolation_data["k_values_matrix"]),
    method="linear",
    bounds_error=False,
    fill_value=None
)

_UC = UnitConverter()


# =====================================================================
# ПРИВАТНЫЕ ВЫЧИСЛИТЕЛЬНЫЕ БЛОКИ (Соблюдение SRP)
# =====================================================================

def _get_heat_of_vaporization(temperature: float) -> float:
    """Эмпирическая аппроксимация скрытой теплоты парообразования."""
    return (30 - temperature) * 0.582 + 580.4


def _calc_geometry(params: dict) -> dict:
    """Шаг 1: Расчет геометрических характеристик аппарата."""
    d_in = params['diameter_inside_of_pipes']
    s_w = params['thickness_pipe_wall']
    L = params['length_cooling_tubes_of_the_main_bundle']
    N_main = params['number_cooling_tubes_of_the_main_bundle']
    N_extra = params.get('number_cooling_tubes_of_the_built_in_bundle', 0)
    lambda_mat = params['thermal_conductivity_cooling_surface_tube_material']
    
    # Расчет количества трубок воздухоохладителя (~15% если не задано)
    N_total_air = params.get('number_air_cooler_total_pipes', (N_main + N_extra) * 0.15)

    d_out = d_in + 2 * s_w
    area_total = (math.pi * L * N_main * d_out * 1e-6)
    area_air = (math.pi * L * N_total_air * d_out * 1e-6)

    # Коэффициент влияния воздухоохладителя
    Kf = 1 - 0.225 * (area_air / area_total) if area_total > 0 else 1.0
    
    # Термическое сопротивление стенки трубы
    R1 = ((2 * s_w / 1000 * d_out / 1000) / ((d_out / 1000 + d_in / 1000) * lambda_mat))

    return {
        'd_out': d_out, 
        'area_total': area_total, 
        'area_air': area_air, 
        'Kf': Kf, 
        'R1': R1,
        'N_total': N_main + N_extra
    }


def _calc_thermohydraulics(params: dict, d_in: float, N_total: int) -> dict:
    """Шаг 2: Расчет скоростей и температур охлаждающей воды."""
    m_cw = params['mass_flow_cooling_water']
    n_passes = params['number_cooling_water_passes_of_the_main_bundle']
    T_cw1 = params['temperature_cooling_water_1']
    m_flow = params['mass_flow_flow_path_1']
    dryness = params['degree_dryness_flow_path_1']

    speed = (m_cw * n_passes) / (900 * math.pi * N_total * (d_in / 1000) ** 2)
    r_vap = _get_heat_of_vaporization(T_cw1)

    dT = (m_flow * r_vap * dryness) / m_cw
    T_cw2 = T_cw1 + dT
    T_avg = (T_cw1 + T_cw2) / 2

    return {
        'speed': speed, 
        'r_vap': r_vap, 
        'dT': dT, 
        'T_cw2': T_cw2, 
        'T_avg': T_avg
    }


def _calc_heat_transfer_coefficient(speed: float, T_avg: float, Kf: float, R1: float, b: float) -> dict:
    """Шаг 3: Определение финального коэффициента теплопередачи (K)."""
    # Билинейная интерполяция по матрице Метро-Виккерса
    K_temp = _INTERPOLATOR((speed, T_avg)).item()

    # 0.85 - поправка Метро-Виккерса, 0.087/10000 - стандартное термическое сопротивление
    denom_clean = (1 / (K_temp * 0.85 * const.coefficient_B_const * Kf)) - 0.087 / 10000 + R1
    K_clean = 1 / denom_clean
    
    R = (1 / K_clean) * ((1 / b) - 1)
    K_zag = 1 / (denom_clean + R)

    return {
        'K_temp': K_temp, 
        'K_clean': K_clean, 
        'R': R, 
        'K_zag': K_zag
    }


# =====================================================================
# ПУБЛИЧНОЕ API (Оркестрация)
# =====================================================================

def calculate_pressure(params: dict) -> dict:
    """
    Вычисляет давление в конденсаторе для одной конкретной точки (режима).
    
    Делегирует расчеты изолированным приватным блокам (_calc_geometry, 
    _calc_thermohydraulics, _calc_heat_transfer_coefficient), объединяя 
    их результаты в итоговый ответ.

    Args:
        params (dict): Плоский словарь входных параметров.

    Returns:
        dict: Промежуточные коэффициенты и финальное давление ('p_kgf').
    """
    # 1. Вычисляем геометрию
    geom = _calc_geometry(params)
    
    # 2. Вычисляем термогидравлику
    thermo = _calc_thermohydraulics(
        params, 
        d_in=params['diameter_inside_of_pipes'], 
        N_total=geom['N_total']
    )
    
    # 3. Вычисляем теплопередачу
    heat_transfer = _calc_heat_transfer_coefficient(
        speed=thermo['speed'], 
        T_avg=thermo['T_avg'], 
        Kf=geom['Kf'], 
        R1=geom['R1'], 
        b=params.get('coefficient_b', 1.0)
    )

    # 4. Расчет температуры и давления насыщения (IF97)
    m_cw = params['mass_flow_cooling_water']
    T_cw1 = params['temperature_cooling_water_1']
    
    delta_T_rel = 1 / (math.e ** ((heat_transfer['K_zag'] * geom['area_total']) / (m_cw * 1000)) - 1)
    T_sat = thermo['T_cw2'] + delta_T_rel * (thermo['T_cw2'] - T_cw1)
    
    p_MPa = seuif97.tx2p(T_sat, 1)
    p_kgf = _UC.convert(p_MPa, from_unit="МПа", to_unit="кгс/см²", parameter_type="pressure")

    # 5. Сборка результатов
    result = {
        'delta_T_rel': delta_T_rel,
        'T_sat': T_sat, 
        'p_kgf': p_kgf
    }
    result.update(geom)
    result.update(thermo)
    result.update(heat_transfer)

    return result


def batch_calculate(params_template: dict, varying_params: dict) -> list[dict]:
    """
    Выполняет пакетный расчет (генерацию матриц) методом Метро-Виккерса.

    Функция перебирает все возможные комбинации (Декартово произведение) 
    изменяемых параметров и вызывает calculate_pressure для каждой точки.

    Args:
        params_template (dict): Базовый словарь параметров (геометрия, константы).
        varying_params (dict): Словарь списков, где ключ - имя параметра, 
            а значение - список (массив) значений для итерации.

    Returns:
        list[dict]: Плоский список результатов.
    """
    keys = list(varying_params.keys())
    values = list(varying_params.values())

    results = []
    for combo in product(*values):
        params = params_template.copy()
        params.update(dict(zip(keys, combo, strict=True)))
        
        res = calculate_pressure(params)
        res.update(dict(zip(keys, combo, strict=True)))
        results.append(res)

    return results