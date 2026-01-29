import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import List, Dict, Any


class VKUStrategy:
    """
    Класс для расчета давления в воздушно-конденсационной установке (ВКУ).
    Методика основана на определении давления по приведенному расходу пара
    и температуре наружного воздуха с использованием 2D-интерполяции.
    """
    _TVOZD_CONST_DEFAULT = 20.0
    _P_DATA: List = [
        [40, 35, 30, 25, 20],
        [40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140],
        [
            [0.104011054, 0.080455609, 0.061998746, 0.046804974, 0.036709784],
            [0.111862869, 0.086879821, 0.067199298, 0.050985811, 0.039972876],
            [0.119918627, 0.093100090, 0.072297880, 0.055880448, 0.043847797],
            [0.127974385, 0.099830217, 0.077498432, 0.060367200, 0.047416804],
            [0.136743944, 0.106968231, 0.083718701, 0.065567752, 0.051597640],
            [0.145819418, 0.114718074, 0.090142913, 0.070360419, 0.056186363],
            [0.155812637, 0.123181719, 0.097280927, 0.075866886, 0.060673115],
            [0.165805856, 0.131543391, 0.104418940, 0.081373354, 0.065873667],
            [0.176512876, 0.140618866, 0.112168783, 0.087899538, 0.071686050],
            [0.187525812, 0.150000255, 0.119918627, 0.094323750, 0.077498432],
            [0.198232832, 0.159381644, 0.127668470, 0.101155848, 0.083718701]
        ]
    ]

    def __init__(self, mass_flow_steam_nom: float, degree_dryness_steam_nom: float):
        if mass_flow_steam_nom <= 0:
            raise ValueError("Номинальный расход пара (mass_flow_steam_nom) должен быть больше нуля.")
        if not (0 < degree_dryness_steam_nom <= 1):
            raise ValueError("Номинальная степень сухости (degree_dryness_steam_nom) должна быть в диапазоне (0, 1].")

        self.mass_flow_steam_nom = mass_flow_steam_nom
        self.degree_dryness_steam_nom = degree_dryness_steam_nom

        self._interpolator = self._create_interpolator()

    def _create_interpolator(self) -> RegularGridInterpolator:
        t_air_axis_desc = np.array(self._P_DATA[0])
        g_reduced_axis = np.array(self._P_DATA[1])
        p_values = np.array(self._P_DATA[2])

        if t_air_axis_desc[0] > t_air_axis_desc[-1]:
            t_air_axis_asc = np.flip(t_air_axis_desc)
            p_values_reordered = np.fliplr(p_values)
        else:
            t_air_axis_asc = t_air_axis_desc
            p_values_reordered = p_values

        return RegularGridInterpolator(
            (g_reduced_axis, t_air_axis_asc),
            p_values_reordered,
            bounds_error=False,
            fill_value=None
        )

    def calculate(self, params: Dict[str, Any]) -> Dict[str, float]:
        """
        Выполняет расчет давления в конденсаторе.

        Args:
            params (Dict[str, Any]): Словарь с входными параметрами.
                Обязательные ключи:
                - 'mass_flow_flow_path_1' (float): G1, текущий расход пара [т/ч].
                - 'degree_dryness_flow_path_1' (float): X1, текущая степень сухости.
                Опциональный ключ:
                - 'temperature_air' (float): tвозд, температура наружного воздуха [°C].

        Returns:
            Dict[str, float]: Словарь с результатами расчета.
                - 'pressure_flow_path_1': P1, рассчитанное давление в конденсаторе [кгс/см²].
                - 'mass_flow_reduced_steam_condencer': Gк_прив, приведенный расход [%].

        Raises:
            KeyError: Если в словаре `params` отсутствует обязательный ключ.
        """
        try:
            mass_flow_flow_path_1 = params['mass_flow_flow_path_1']
            degree_dryness_flow_path_1 = params['degree_dryness_flow_path_1']
        except KeyError as e:
            raise KeyError(f"Отсутствует обязательный параметр в словаре: {e}")

        t_air = params.get('temperature_air', self._TVOZD_CONST_DEFAULT)

        mass_flow_reduced_steam_condencer = (
                (mass_flow_flow_path_1 / self.mass_flow_steam_nom) *
                (degree_dryness_flow_path_1 / self.degree_dryness_steam_nom) * 100
        )

        point_to_interpolate = (mass_flow_reduced_steam_condencer, t_air)
        pressure_flow_path_1 = self._interpolator(point_to_interpolate).item()

        results = {
            'pressure_flow_path_1': pressure_flow_path_1,
            'mass_flow_reduced_steam_condencer': mass_flow_reduced_steam_condencer
        }

        return results
