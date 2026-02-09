from __future__ import annotations

import logging
from math import pi, sqrt

# IF97
from seuif97 import ph, ph2t, ph2v, pt2h

# Вспомогательные (наши)
from WSAProperties import air_calc, ksi_calc, lambda_calc

# Схемы pydantic/dataclass'ы
from app.schemas import CalculationParams, CalculationResult, ValveInfo


# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ------------------------- Исключение домена расчёта ------------------------- #
class CalculationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# ----------------------------- Утилиты и единицы ----------------------------- #
def convert_to_meters(value: float, description: str) -> float:
    """
    Конвертирует значение из мм в метры.
    """
    if value is None:
        raise CalculationError(f"Нет данных о {description}")
    return float(value) / 1000.0


def calculate_enthalpy_for_air(t_air_c: float) -> float:
    """
    Энтальпия воздуха (приближение): h ≈ 1.006 * t (кДж/кг), t — °C.
    """
    return float(t_air_c) * 1.006


def convert_pressure_to_mpa(pressure: float, unit: int = 3) -> float:
    """
    Перевод давления -> МПа.

    unit:
      1 - Па        -> МПа
      2 - кПа       -> МПа
      3 - кгс/см²   -> МПа (по умолчанию)
      4 - атм (тех) -> МПа
      5 - бар       -> МПа
      6 - атм (физ) -> МПа
    """
    conversion_factors = {
        1: 1e-6,        # Pa -> MPa
        2: 1e-3,        # kPa -> MPa
        3: 0.0980665,   # kgf/cm^2 -> MPa
        4: 0.0980665,   # at (техническая атмосфера) -> MPa
        5: 0.1,         # bar -> MPa
        6: 0.101325,    # atm (физическая) -> MPa
    }
    try:
        factor = conversion_factors[unit]
    except KeyError:
        raise CalculationError(f"Неверный выбор единицы измерения давления: {unit}")
    return float(pressure) * factor


def _expected_suctions(count_parts: int) -> int:
    """
    Сколько нужно давлений отсоса эжектора по числу участков:
      2 -> 1, 3 -> 1, 4 -> 2, 5 -> 3
    """
    if count_parts <= 1:
        return 0
    if count_parts == 2:
        return 1
    return max(count_parts - 2, 0)


def _suction_index_for_area(count_parts: int, area_n: int) -> int:
    """
    Индекс давления отсоса для участка area_n.
    """
    if area_n == 2:
        return 0
    if area_n == 3:
        return 0 if count_parts == 3 else 1
    if area_n == 4:
        return 1 if count_parts == 4 else 2
    if area_n == 5:
        return 2
    raise CalculationError(f"Нет отсоса для участка {area_n} при count_parts={count_parts}")


# ---------------------- Гидравлика зазора и расчёт расхода ---------------------- #
def _compute_G(last_part: bool, alpha: float, p1_pa: float, p2_pa: float, v: float, area_S: float) -> float:
    """
    Массовый расход G (т/ч) через кольцевой зазор.
    Давления — в Паскалях, v — м^3/кг, S — м^2.
    """
    under_root = (p1_pa ** 2 - p2_pa ** 2) / (p1_pa * v)
    if under_root <= 0:
        # При некорректных данных / единицах подкоренное может стать <=0
        raise CalculationError(f"Отрицательное/нулевое выражение под корнем: {under_root:.3e}")
    g_t_per_h = alpha * area_S * sqrt(under_root) * 3.6  # кг/с -> т/ч (делим на 3.6 при обратном переводе)
    if last_part:
        g_t_per_h = max(0.001, g_t_per_h)
    return g_t_per_h


def _part_props_detection(
    p_first_mpa: float,
    p_second_mpa: float,
    v: float,
    dyn_viscosity: float,
    len_part_m: float,
    delta_clearance_m: float,
    area_S: float,
    ksi: float,
    last_part: bool = False,
    w_min: float = 1.0,
    w_max: float = 1000.0,
) -> float:
    """
    Бинарный поиск скорости в зазоре по уравнению с учётом трения и местных сопротивлений.
    Возвращает массовый расход G (т/ч).
    seuif97 — в МПа, тут внутри переводим МПа -> Па для формулы.
    """
    if p_first_mpa <= p_second_mpa:
        if abs(p_first_mpa - p_second_mpa) < 1e-9:
            p_first_mpa += 0.003  # «разлепление» как в старом коде (в МПа)
        else:
            raise CalculationError(
                f"Для течения нужно P_first > P_second: p1={p_first_mpa:.6f} MPa, p2={p_second_mpa:.6f} MPa"
            )

    if area_S <= 0 or delta_clearance_m <= 0 or len_part_m <= 0:
        raise CalculationError("Некорректная геометрия участка (S, delta_clearance, len_part должны быть > 0)")

    # МПа -> Па
    p1_pa = p_first_mpa * 1e6
    p2_pa = p_second_mpa * 1e6

    # Кинематическая вязкость ν = μ / ρ; v = 1/ρ => ν = μ * v
    kin_vis = v * dyn_viscosity
    if kin_vis <= 0:
        raise CalculationError(f"Кинематическая вязкость должна быть > 0, получено: {kin_vis:.3e}")

    # Поиск скорости
    iters = 0
    while (w_max - w_min) > 1e-3:
        w_mid = 0.5 * (w_min + w_max)
        re = (w_mid * 2.0 * delta_clearance_m) / kin_vis
        lam = lambda_calc(re)
        alpha = 1.0 / sqrt(1.0 + ksi + (0.5 * lam * len_part_m) / delta_clearance_m)

        g = _compute_G(last_part, alpha, p1_pa, p2_pa, v, area_S)               # т/ч
        w_calc = v * (g / 3.6) / area_S                                         # м/с

        if (w_mid - w_calc) > 0.0:
            w_max = w_mid
        else:
            w_min = w_mid

        iters += 1
        if iters > 1000:  # предохранитель
            break

    # Финал
    w_res = 0.5 * (w_min + w_max)
    re = (w_res * 2.0 * delta_clearance_m) / kin_vis
    lam = lambda_calc(re)
    alpha = 1.0 / sqrt(1.0 + ksi + (0.5 * lam * len_part_m) / delta_clearance_m)
    g = _compute_G(last_part, alpha, p1_pa, p2_pa, v, area_S)

    logger.debug(
        "part: p1=%.6f MPa, p2=%.6f MPa, len=%.4f m, v=%.6f, mu=%.3e, Re=%.2f, λ=%.5f, α=%.5f, G=%.6f t/h",
        p_first_mpa, p_second_mpa, len_part_m, v, dyn_viscosity, re, lam, alpha, g
    )
    return g


# --------------------------- Основной класс расчёта --------------------------- #
class ValveCalculator:
    """
    Расчёт расходов по участкам клапана (пар/воздух) и параметров отсосов (деаэратор/эжектор).
    Входные давления — по умолчанию в кгс/см²; seuif97 — в МПа; формула G — в Па.
    """

    def __init__(self, params: CalculationParams, valve_info: ValveInfo):
        self.params = params
        self.valve_info = valve_info

        try:
            # Базовые параметры
            self.temperature_start = float(params.temperature_start)  # °C (для пара)
            self.t_air = float(params.t_air)                          # °C
            self.h_air = calculate_enthalpy_for_air(self.t_air)
            self.count_valves = int(params.count_valves)

            # Геометрия (мм -> м)
            self.radius_rounding = convert_to_meters(valve_info.round_radius, "радиусе скругления")
            self.delta_clearance = convert_to_meters(valve_info.clearance, "зазоре")
            self.diameter_stock = convert_to_meters(valve_info.diameter, "диаметре штока")

            # Длины участков (берём подряд, без дыр)
            raw_lengths = list(getattr(valve_info, "section_lengths", []) or [])
            if not raw_lengths:
                raise CalculationError("Не заданы длины участков клапана.")
            self.len_parts: list[float] = []
            for i, L in enumerate(raw_lengths):
                if L is None:
                    break
                self.len_parts.append(convert_to_meters(L, f"участке {i + 1}"))
            self.count_parts: int = len(self.len_parts)
            if self.count_parts < 2:
                raise CalculationError("Клапан должен иметь как минимум два участка.")

            # Единицы входных давлений пользователя
            pressure_unit_input = getattr(params, "pressure_unit", 3)  # по умолчанию: кгс/см²

            # Давления по участкам (-> МПа)
            p_values_in = list(params.p_values[: self.count_parts])
            if len(p_values_in) != self.count_parts:
                raise CalculationError(
                    f"Количество давлений P ({len(p_values_in)}) должно совпадать с числом участков ({self.count_parts})"
                )
            if any(p <= 0 for p in p_values_in):
                raise CalculationError("Все входные давления по участкам должны быть > 0.")

            self.P_values: list[float] = [convert_pressure_to_mpa(p, unit=pressure_unit_input) for p in p_values_in]

            # Давление в деаэратор: берём P2
            self.p_deaerator: float = self.P_values[1]

            # Давления отсосов эжектора (-> МПа)
            p_suctions_raw = list(getattr(params, "p_ejector", []) or [])
            self.p_suctions: list[float] = [convert_pressure_to_mpa(p, unit=pressure_unit_input) for p in p_suctions_raw]

            need_suctions = _expected_suctions(self.count_parts)
            if len(self.p_suctions) < need_suctions:
                raise CalculationError(
                    f"Ожидалось не меньше {need_suctions} давлений отсоса, получено {len(self.p_suctions)}."
                )

            # Производные величины
            self.proportional_coef = self.radius_rounding / (2.0 * self.delta_clearance)
            self.S = self.delta_clearance * pi * self.diameter_stock            # площадь зазора
            if self.S <= 0:
                raise CalculationError("Площадь зазора S должна быть > 0.")
            self.KSI = ksi_calc(self.proportional_coef)

            # Термопараметры пара на входе 1-го участка
            self.enthalpy_steam = pt2h(self.P_values[0], self.temperature_start)

            # Массивы по участкам
            self.g_parts = [0.0] * self.count_parts
            self.t_parts = [0.0] * self.count_parts
            self.h_parts = [0.0] * self.count_parts
            self.v_parts = [0.0] * self.count_parts
            self.din_vis_parts = [0.0] * self.count_parts

            # Текущее давление эжектора (в ходе расчётов)
            self.p_ejector: float | None = None

            # Лог входных
            logger.info(
                "INIT: parts=%d, valves=%d, P_in(MPa)=%s, p_suctions(MPa)=%s, lengths(m)=%s, "
                "delta=%.6f m, D=%.6f m, S=%.6e m^2, KSI=%.5f, T0=%.1f C, t_air=%.1f C, unit=%d",
                self.count_parts, self.count_valves,
                [round(x, 6) for x in self.P_values],
                [round(x, 6) for x in self.p_suctions],
                [round(x, 6) for x in self.len_parts],
                self.delta_clearance, self.diameter_stock, self.S, self.KSI,
                self.temperature_start, self.t_air, pressure_unit_input
            )

        except CalculationError:
            raise
        except Exception as e:
            logger.exception("Ошибка инициализации расчётчика")
            raise CalculationError(f"Ошибка при инициализации: {e}")

    # --------------------------- Основной сценарий --------------------------- #
    def perform_calculations(self) -> CalculationResult:
        try:
            # Расчёты по участкам
            for i in range(self.count_parts):
                getattr(self, f"calculate_area{i + 1}")()

            # Отсосы
            dea_g, dea_t, dea_h, dea_p = self.deaerator_options()
            ej_g, ej_t, ej_h, ej_p = self.ejector_options()

            self.P_values = [p / 0.0980665 for p in self.P_values]

            result_payload = {
                "Gi": self.g_parts[: self.count_parts],
                "Pi_in": self.P_values[: self.count_parts],
                "Ti": self.t_parts[: self.count_parts],
                "Hi": self.h_parts[: self.count_parts],
                "deaerator_props": [dea_g, dea_t, dea_h, dea_p],
                "ejector_props": [
                    {"g": g, "t": t, "h": h, "p": p}
                    for g, t, h, p in zip(ej_g, ej_t, ej_h, ej_p, strict=True)
                ],
            }

            # Сводный лог
            print(result_payload)
            self._log_summary(result_payload)

            return CalculationResult(**result_payload)
        except CalculationError:
            raise
        except Exception as e:
            logger.exception("Ошибка во время расчёта")
            raise CalculationError(f"Ошибка в расчётах: {e}")

    # --------------------------- Расчёты по участкам --------------------------- #
    def calculate_area1(self) -> None:
        logger.info("Расчёт участка 1")

        if self.count_parts < 2:
            raise CalculationError("Клапан должен иметь как минимум два участка.")
        if not self.len_parts[0] or not self.len_parts[1]:
            raise CalculationError("Длины первого и второго участков должны быть заданы и > 0.")

        # Пар
        self.h_parts[0] = self.enthalpy_steam
        self.v_parts[0] = ph2v(self.P_values[0], self.h_parts[0])
        self.t_parts[0] = ph2t(self.P_values[0], self.h_parts[0])
        self.din_vis_parts[0] = ph(self.P_values[0], self.h_parts[0], 24)

        self.g_parts[0] = _part_props_detection(
            self.P_values[0], self.P_values[1],
            self.v_parts[0], self.din_vis_parts[0],
            self.len_parts[0], self.delta_clearance, self.S, self.KSI,
        )

        logger.info(
            "Area1: G=%.6f t/h, T=%.2f C, H=%.4f kJ/kg, v=%.6f m3/kg",
            self.g_parts[0], self.t_parts[0], self.h_parts[0], self.v_parts[0]
        )

    def calculate_area2(self) -> None:
        logger.info("Расчёт участка 2")
        if self.count_parts < 2:
            return

        idx = _suction_index_for_area(self.count_parts, 2)
        self.p_ejector = self.p_suctions[idx]

        if self.count_parts > 2:
            # Пар до следующего участка
            self.h_parts[1] = self.enthalpy_steam
            self.v_parts[1] = ph(self.P_values[1], self.h_parts[1], 3)
            self.t_parts[1] = ph(self.P_values[1], self.h_parts[1], 1)
            self.din_vis_parts[1] = ph(self.P_values[1], self.h_parts[1], 24)

            self.g_parts[1] = _part_props_detection(
                self.P_values[1], self.p_ejector,
                self.v_parts[1], self.din_vis_parts[1],
                self.len_parts[1], self.delta_clearance, self.S, self.KSI,
            )
        else:
            # Два участка: участок 2 — воздух (последний)
            # Пересчёт участка 1 на конечное давление эжектора
            self.h_parts[0] = self.enthalpy_steam
            self.v_parts[0] = ph2v(self.P_values[0], self.h_parts[0])
            self.t_parts[0] = ph2t(self.P_values[0], self.h_parts[0])
            self.din_vis_parts[0] = ph(self.P_values[0], self.h_parts[0], 24)

            self.g_parts[0] = _part_props_detection(
                self.P_values[0], self.p_ejector,
                self.v_parts[0], self.din_vis_parts[0],
                self.len_parts[0], self.delta_clearance, self.S, self.KSI,
            )

            # Воздух
            self.h_parts[1] = self.h_air
            self.t_parts[1] = self.t_air
            self.v_parts[1] = air_calc(self.t_parts[1], 1)
            self.din_vis_parts[1] = air_calc(self.t_parts[1], 2)

            self.g_parts[1] = _part_props_detection(
                0.1013, self.p_ejector,                   # МПа: атмосферное -> эжектор
                self.v_parts[1], self.din_vis_parts[1],
                self.len_parts[1], self.delta_clearance, self.S, self.KSI,
                last_part=True,
            )

        logger.info(
            "Area2: G=%.6f t/h, T=%.2f C, H=%.4f kJ/kg, v=%.6f m3/kg",
            self.g_parts[1], self.t_parts[1], self.h_parts[1], self.v_parts[1]
        )

    def calculate_area3(self) -> None:
        logger.info("Расчёт участка 3")
        if self.count_parts < 3:
            return

        idx = _suction_index_for_area(self.count_parts, 3)
        self.p_ejector = self.p_suctions[idx]

        if self.count_parts > 3:
            # Пар
            self.h_parts[2] = self.enthalpy_steam
            self.v_parts[2] = ph(self.P_values[2], self.h_parts[2], 3)
            self.t_parts[2] = ph(self.P_values[2], self.h_parts[2], 1)
            self.din_vis_parts[2] = ph(self.P_values[2], self.h_parts[2], 24)

            self.g_parts[2] = _part_props_detection(
                self.P_values[2], self.p_ejector,
                self.v_parts[2], self.din_vis_parts[2],
                self.len_parts[2], self.delta_clearance, self.S, self.KSI,
            )
        else:
            # Воздух (последний)
            self.h_parts[2] = self.h_air
            self.t_parts[2] = self.t_air
            self.v_parts[2] = air_calc(self.t_parts[2], 1)
            self.din_vis_parts[2] = air_calc(self.t_parts[2], 2)

            self.g_parts[2] = _part_props_detection(
                0.1013, self.p_ejector,
                self.v_parts[2], self.din_vis_parts[2],
                self.len_parts[2], self.delta_clearance, self.S, self.KSI,
                last_part=True,
            )

        logger.info(
            "Area3: G=%.6f t/h, T=%.2f C, H=%.4f kJ/kg, v=%.6f m3/kg",
            self.g_parts[2], self.t_parts[2], self.h_parts[2], self.v_parts[2]
        )

    def calculate_area4(self) -> None:
        logger.info("Расчёт участка 4")
        if self.count_parts < 4:
            return

        idx = _suction_index_for_area(self.count_parts, 4)
        self.p_ejector = self.p_suctions[idx]

        if self.count_parts > 4:
            # Пар
            self.h_parts[3] = self.enthalpy_steam
            self.v_parts[3] = ph(self.P_values[3], self.h_parts[3], 3)
            self.t_parts[3] = ph(self.P_values[3], self.h_parts[3], 1)
            self.din_vis_parts[3] = ph(self.P_values[3], self.h_parts[3], 24)

            self.g_parts[3] = _part_props_detection(
                self.P_values[3], self.p_ejector,
                self.v_parts[3], self.din_vis_parts[3],
                self.len_parts[3], self.delta_clearance, self.S, self.KSI,
            )
        else:
            # Воздух (последний)
            self.h_parts[3] = self.h_air
            self.t_parts[3] = self.t_air
            self.v_parts[3] = air_calc(self.t_parts[3], 1)
            self.din_vis_parts[3] = air_calc(self.t_parts[3], 2)

            self.g_parts[3] = _part_props_detection(
                0.1013, self.p_ejector,
                self.v_parts[3], self.din_vis_parts[3],
                self.len_parts[3], self.delta_clearance, self.S, self.KSI,
                last_part=True,
            )

        logger.info(
            "Area4: G=%.6f t/h, T=%.2f C, H=%.4f kJ/kg, v=%.6f m3/kg",
            self.g_parts[3], self.t_parts[3], self.h_parts[3], self.v_parts[3]
        )

    def calculate_area5(self) -> None:
        logger.info("Расчёт участка 5")
        if self.count_parts < 5:
            return

        idx = _suction_index_for_area(self.count_parts, 5)
        self.p_ejector = self.p_suctions[idx]

        # Воздух
        self.h_parts[4] = self.h_air
        self.t_parts[4] = self.t_air
        self.v_parts[4] = air_calc(self.t_parts[4], 1)
        self.din_vis_parts[4] = air_calc(self.t_parts[4], 2)

        self.g_parts[4] = _part_props_detection(
            0.1013, self.p_ejector,
            self.v_parts[4], self.din_vis_parts[4],
            self.len_parts[4], self.delta_clearance, self.S, self.KSI,
            last_part=True,
        )

        logger.info(
            "Area5: G=%.6f t/h, T=%.2f C, H=%.4f kJ/kg, v=%.6f m3/kg",
            self.g_parts[4], self.t_parts[4], self.h_parts[4], self.v_parts[4]
        )

    # --------------------------- Отсосы: деаэратор/эжектор --------------------------- #
    def deaerator_options(self) -> tuple[float, float, float, float]:
        """
        Отсос в деаэратор. Возвращает (g, t, h, p).
        """
        if self.count_parts < 2:
            return 0.0, 0.0, 0.0, 0.0

        h_dea = self.h_parts[1]
        p_dea = self.p_deaerator

        if self.count_parts == 2:
            # для 2 участков деаэратор не считается
            return 0.0, 0.0, h_dea, p_dea

        if self.count_parts == 3:
            g = (self.g_parts[0] - self.g_parts[1]) * self.count_valves
        elif self.count_parts == 4:
            g = (self.g_parts[0] - self.g_parts[1] - self.g_parts[2]) * self.count_valves
        elif self.count_parts == 5:
            g = (self.g_parts[0] - self.g_parts[1] - self.g_parts[2] - self.g_parts[3]) * self.count_valves
        else:
            raise CalculationError("Неверное количество участков для деаэратора.")

        t_dea = ph(p_dea, h_dea, 1)
        p_dea /= 0.0980665
        logger.info("Deaerator: g=%.6f, t=%.2f, h=%.4f, p=%.6f", g, t_dea, h_dea, p_dea)
        return g, t_dea, h_dea, p_dea

    def ejector_options(self) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
        """
        Отсосы в эжектор(ы).
        Возвращает кортеж списков одинаковой длины: (g_list, t_list, h_list, p_list).
        """
        n = _expected_suctions(self.count_parts)
        g_list = [0.0] * n
        t_list = [0.0] * n
        h_list = [0.0] * n
        p_list = [0.0] * n

        if n == 0:
            return tuple(g_list), tuple(t_list), tuple(h_list), tuple(p_list)

        if self.count_parts == 2:
            den = max(self.g_parts[1] + self.g_parts[0], 1e-9)
            g_list[0] = (self.g_parts[1] + self.g_parts[0]) * self.count_valves
            h_list[0] = (self.h_parts[1] * self.g_parts[1] + self.h_parts[0] * self.g_parts[0]) / den
            p_list[0] = self.p_suctions[0]
            t_list[0] = ph(p_list[0], h_list[0], 1)

        elif self.count_parts == 3:
            den = max(self.g_parts[2] + self.g_parts[1], 1e-9)
            g_list[0] = (self.g_parts[2] + self.g_parts[1]) * self.count_valves
            h_list[0] = (self.h_parts[2] * 4.1868 * self.g_parts[2] + self.h_parts[1] * self.g_parts[1]) / den
            p_list[0] = self.p_suctions[0]
            t_list[0] = ph(p_list[0], h_list[0], 1)

        elif self.count_parts == 4:
            # Первый отсос: (G2 - G3 - G4), энтальпия = h2
            g1 = max(self.g_parts[1] - self.g_parts[2] - self.g_parts[3], 0.0) * self.count_valves
            h1 = self.h_parts[1]
            p1 = self.p_suctions[0]
            t1 = ph(p1, h1, 1)

            # Второй отсос: |G3 - G4|, энтальпия смеси (h3/h4)
            den2 = max(self.g_parts[3] + self.g_parts[2], 1e-9)
            g2 = abs(self.g_parts[2] - self.g_parts[3]) * self.count_valves
            h2 = (self.h_parts[3] * self.g_parts[3] + self.h_parts[2] * self.g_parts[2]) / den2
            p2 = self.p_suctions[1]
            t2 = ph(p2, h2, 1)

            g_list[:2] = [g1, g2]
            h_list[:2] = [h1, h2]
            p_list[:2] = [p1, p2]
            t_list[:2] = [t1, t2]

        elif self.count_parts == 5:
            # Первый отсос: (G2 - G3 - G4), энтальпия = h2
            g1 = max(self.g_parts[1] - self.g_parts[2] - self.g_parts[3], 0.0) * self.count_valves
            h1 = self.h_parts[1]
            p1 = self.p_suctions[0]
            t1 = ph(p1, h1, 1)

            # Второй отсос: |G3 - G4|, энтальпия = h2 (как в старой логике)
            g2 = abs(self.g_parts[2] - self.g_parts[3]) * self.count_valves
            h2 = self.h_parts[1]
            p2 = self.p_suctions[1]
            t2 = ph(p2, h2, 1)

            # Третий отсос: (G4 + G5), энтальпия смеси (h4/h5)
            den3 = max(self.g_parts[4] + self.g_parts[3], 1e-9)
            g3 = (self.g_parts[3] + self.g_parts[4]) * self.count_valves
            h3 = (self.h_parts[4] * self.g_parts[4] + self.h_parts[3] * self.g_parts[3]) / den3
            p3 = self.p_suctions[2]
            t3 = ph(p3, h3, 1)

            g_list[:3] = [g1, g2, g3]
            h_list[:3] = [h1, h2, h3]
            p_list[:3] = [p1, p2, p3]
            t_list[:3] = [t1, t2, t3]

        else:
            raise CalculationError("Неверное количество участков для эжектора.")

        # Лог по каждому отсосу
        for i in range(n):
            logger.info("Ejector #%d: g=%.6f, t=%.2f, h=%.4f, p=%.6f", i + 1, g_list[i], t_list[i], h_list[i], p_list[i])

        p_list = [p / 0.0980665 for p in p_list]
        return tuple(g_list), tuple(t_list), tuple(h_list), tuple(p_list)

    # ------------------------------ Сводный лог ------------------------------ #
    def _log_summary(self, payload: dict) -> None:
        gi = tuple(round(x, 6) for x in payload["Gi"])
        pi = tuple(round(x, 6) for x in payload["Pi_in"])
        ti = tuple(round(x, 6) for x in payload["Ti"])
        hi = tuple(round(x, 6) for x in payload["Hi"])

        dea_g, dea_t, dea_h, dea_p = payload["deaerator_props"]

        logger.info("SUMMARY -> Gi: %s", gi)
        logger.info("SUMMARY -> Pi_in: %s", pi)
        logger.info("SUMMARY -> Ti: %s", ti)
        logger.info("SUMMARY -> Hi: %s", hi)
        logger.info("SUMMARY -> deaerator props: (g=%.6f, t=%.6f, h=%.6f, p=%.6f)", dea_g, dea_t, dea_h, dea_p)

        ej_props = payload["ejector_props"]
        if not ej_props:
            logger.info("SUMMARY -> ejector props: []")
        elif len(ej_props) == 1:
            ej = ej_props[0]
            logger.info(
                "SUMMARY -> ejector props: (g=%.6f, t=%.6f, h=%.6f, p=%.6f)",
                ej["g"], ej["t"], ej["h"], ej["p"]
            )
        else:
            for idx, ej in enumerate(ej_props, start=1):
                logger.info(
                    "SUMMARY -> ejector #%d props: (g=%.6f, t=%.6f, h=%.6f, p=%.6f)",
                    idx, ej["g"], ej["t"], ej["h"], ej["p"]
                )
