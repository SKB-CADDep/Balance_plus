"""
Модуль табличной стратегии расчета давления (Table Pressure Strategy - TPS).

Реализует альтернативный алгоритм определения абсолютного давления в конденсаторе.
Основан на двумерной и одномерной интерполяции эмпирических блоков данных 
(NAMET и NAMED). Метод рассчитывает два возможных значения давления и 
возвращает наибольшее из них (консервативная оценка).
"""

from typing import Any

import numpy as np
from scipy import interpolate


class TablePressureStrategy:
    """
    Стратегия табличного расчета давления конденсатора.

    Использует функции интерполяции из библиотеки SciPy для извлечения 
    промежуточных значений из переданных наборов нормативных или экспериментальных данных.
    """

    def _create_namet_interpolator(self, namet_data: list) -> interpolate.RectBivariateSpline:
        """
        Создает объект двумерной интерполяции (сплайна) для блока NAMET.

        Математическая особенность: функция `RectBivariateSpline` требует, чтобы
        значения по осям были строго возрастающими. Данный метод автоматически
        распознает убывающий массив оси температур (t_axis_raw) и инвертирует
        его (вместе с матрицей значений), чтобы предотвратить ошибку SciPy.

        Args:
            namet_data (list): Список из трех элементов:
                - index 0: Массив температур (Ось X).
                - index 1: Массив расходов пара (Ось Y).
                - index 2: 2D-матрица значений давления (Ось Z).

        Returns:
            interpolate.RectBivariateSpline: Готовый к использованию 2D-интерполятор 
                (степень сплайна kx=1, ky=1 — билинейная интерполяция).
        """
        t_axis_raw = np.array(namet_data[0])
        g_axis = np.array(namet_data[1])
        values_raw = np.array(namet_data[2])

        # Проверка и инверсия массивов, если температурная ось убывает
        if np.all(np.diff(t_axis_raw) < 0):
            t_axis = t_axis_raw[::-1]
            values = values_raw[::-1, :]
        else:
            t_axis = t_axis_raw
            values = values_raw

        return interpolate.RectBivariateSpline(t_axis, g_axis, values, kx=1, ky=1)

    def _create_named_interpolator(self, named_data: list) -> interpolate.interp1d:
        """
        Создает объект одномерной интерполяции для блока NAMED.

        Args:
            named_data (list): Список из двух элементов:
                - index 0: Массив температур (Ось X).
                - index 1: Массив базовых давлений (Ось Y).

        Returns:
            interpolate.interp1d: Готовый 1D-интерполятор. При выходе за границы 
                оси X используется экстраполяция.
        """
        t_axis = np.array(named_data[0])
        p_axis = np.array(named_data[1])

        return interpolate.interp1d(t_axis, p_axis, bounds_error=False, fill_value="extrapolate")

    def calculate(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Основной метод расчета давления по стратегии TPS.

        Извлекает датасеты NAMET (зависимость от температуры и расхода пара) 
        и NAMED (зависимость только от температуры воды). Выполняет две 
        независимые интерполяции и сравнивает результаты.

        Args:
            params (dict[str, Any]): Словарь, содержащий блоки данных 'NAMET' 
                и 'NAMED', а также вложенный словарь 'inputs' с рабочими 
                режимами (температуры и расходы).

        Returns:
            dict[str, Any]: Словарь с результатами:
                - 'pressure_flow_path_1_NAMET': Давление по 2D-интерполяции.
                - 'pressure_flow_path_1_NAMED': Давление по 1D-интерполяции.
                - 'pressure_flow_path_1': Итоговое выбранное давление (максимум из двух).
        """
        namet_block = params['NAMET']
        namet_data = namet_block['data']
        namet_inputs = params['inputs']

        named_block = params['NAMED']
        named_data = named_block['data']
        named_inputs = params['inputs']

        # Расчет базового давления (1D: только по температуре воды)
        named_interpolator = self._create_named_interpolator(named_data)
        pressure_flow_path_1_NAMED = named_interpolator(
            named_inputs['temperature_cooling_water_1']
        )

        # Расчет комплексного давления (2D: по температуре воды и расходу пара)
        namet_interpolator = self._create_namet_interpolator(namet_data)
        pressure_flow_path_1_NAMET = namet_interpolator(
            namet_inputs['temperature_cooling_water_1'],
            namet_inputs['mass_flow_flow_path_1']
        )[0][0]

        # Бизнес-правило: выбирается максимальное (консервативное) давление
        if pressure_flow_path_1_NAMET >= pressure_flow_path_1_NAMED:
            pressure_flow_path_1 = pressure_flow_path_1_NAMET
        else:
            pressure_flow_path_1 = float(pressure_flow_path_1_NAMED)

        return {
            'pressure_flow_path_1_NAMET': pressure_flow_path_1_NAMET,
            'pressure_flow_path_1_NAMED': float(pressure_flow_path_1_NAMED),
            'pressure_flow_path_1': pressure_flow_path_1
        }