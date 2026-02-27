import logging
from math import pi, sqrt

# IF97
from seuif97 import ph, ph2t, ph2v

# Вспомогательные (наши)
from WSAProperties import air_calc, ksi_calc, lambda_calc

from app.domain.models import RawCalculationResult, ThermoConditions, ValveGeometry


logger = logging.getLogger(__name__)

class PhysicsEngineError(Exception):
    """Специфичная ошибка математического ядра (неверные данные для формул)"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def calculate_enthalpy_for_air(t_air_c: float) -> float:
    """Энтальпия воздуха (приближение): h ≈ 1.006 * t (кДж/кг), t — °C."""
    return float(t_air_c) * 1.006

def _expected_suctions(count_parts: int) -> int:
    """Сколько нужно давлений отсоса эжектора по числу участков."""
    if count_parts <= 1: return 0
    if count_parts == 2: return 1
    return max(count_parts - 2, 0)

def _suction_index_for_area(count_parts: int, area_n: int) -> int:
    if area_n == 2: return 0
    if area_n == 3: return 0 if count_parts == 3 else 1
    if area_n == 4: return 1 if count_parts == 4 else 2
    if area_n == 5: return 2
    raise PhysicsEngineError(f"Нет отсоса для участка {area_n} при count_parts={count_parts}")

def _compute_G(last_part: bool, alpha: float, p1_pa: float, p2_pa: float, v: float, area_S: float) -> float:
    under_root = (p1_pa ** 2 - p2_pa ** 2) / (p1_pa * v)
    if under_root <= 0:
        raise PhysicsEngineError(f"Отрицательное/нулевое выражение под корнем: {under_root:.3e}")
    g_t_per_h = alpha * area_S * sqrt(under_root) * 3.6
    if last_part:
        g_t_per_h = max(0.001, g_t_per_h)
    return g_t_per_h

def _part_props_detection(
    p_first_mpa: float, p_second_mpa: float, v: float, dyn_viscosity: float,
    len_part_m: float, delta_clearance_m: float, area_S: float, ksi: float,
    last_part: bool = False, w_min: float = 1.0, w_max: float = 1000.0,
) -> float:
    if p_first_mpa <= p_second_mpa:
        if abs(p_first_mpa - p_second_mpa) < 1e-9:
            p_first_mpa += 0.003
        else:
            raise PhysicsEngineError(f"Для течения нужно P_first > P_second: p1={p_first_mpa:.6f} MPa, p2={p_second_mpa:.6f} MPa")

    if area_S <= 0 or delta_clearance_m <= 0 or len_part_m <= 0:
        raise PhysicsEngineError("Некорректная геометрия участка (S, delta_clearance, len_part должны быть > 0)")

    p1_pa = p_first_mpa * 1e6
    p2_pa = p_second_mpa * 1e6
    kin_vis = v * dyn_viscosity

    if kin_vis <= 0:
        raise PhysicsEngineError(f"Кинематическая вязкость должна быть > 0, получено: {kin_vis:.3e}")

    iters = 0
    while (w_max - w_min) > 1e-3:
        w_mid = 0.5 * (w_min + w_max)
        re = (w_mid * 2.0 * delta_clearance_m) / kin_vis
        lam = lambda_calc(re)
        alpha = 1.0 / sqrt(1.0 + ksi + (0.5 * lam * len_part_m) / delta_clearance_m)

        g = _compute_G(last_part, alpha, p1_pa, p2_pa, v, area_S)
        w_calc = v * (g / 3.6) / area_S

        if (w_mid - w_calc) > 0.0: w_max = w_mid
        else: w_min = w_mid

        iters += 1
        if iters > 1000: break

    w_res = 0.5 * (w_min + w_max)
    re = (w_res * 2.0 * delta_clearance_m) / kin_vis
    lam = lambda_calc(re)
    alpha = 1.0 / sqrt(1.0 + ksi + (0.5 * lam * len_part_m) / delta_clearance_m)
    return _compute_G(last_part, alpha, p1_pa, p2_pa, v, area_S)


class ValvePhysicsEngine:
    """
    Чистое математическое ядро расчёта расходов и параметров по участкам.
    Ничего не знает про Pydantic, HTTP или пользовательские единицы измерения.
    Все расчеты выполняются строго в базовых величинах (МПа, °C, кДж/кг, метры).
    """

    def __init__(self, geo: ValveGeometry, thermo: ThermoConditions):
        self.geo = geo
        self.thermo = thermo

        try:
            # Геометрические константы
            self.S = geo.clearance_m * pi * geo.diameter_m
            if self.S <= 0:
                raise PhysicsEngineError("Площадь зазора S должна быть > 0.")

            proportional_coef = geo.radius_rounding_m / (2.0 * geo.clearance_m)
            self.KSI = ksi_calc(proportional_coef)

            # Термодинамические константы
            self.h_air = calculate_enthalpy_for_air(thermo.t_air_c)
            self.p_deaerator = thermo.p_in_mpa[1] if len(thermo.p_in_mpa) > 1 else 0.0

            # Инициализация массивов для сохранения результатов по участкам
            n = geo.count_parts
            self.g_parts = [0.0] * n
            self.t_parts = [0.0] * n
            self.h_parts = [0.0] * n
            self.v_parts = [0.0] * n
            self.din_vis_parts = [0.0] * n
            self.p_ejector: float | None = None

        except Exception as e:
            logger.exception("Ошибка инициализации физического движка")
            raise PhysicsEngineError(f"Инициализация провалена: {e}")

    def execute(self) -> RawCalculationResult:
        """Главный метод запуска расчета."""
        try:
            for i in range(self.geo.count_parts):
                getattr(self, f"calculate_area{i + 1}")()

            dea_g, dea_t, dea_h, dea_p = self.deaerator_options()
            ej_g, ej_t, ej_h, ej_p = self.ejector_options()

            ej_results = [
                {"g": g, "t": t, "h": h, "p_mpa": p}
                for g, t, h, p in zip(ej_g, ej_t, ej_h, ej_p, strict=True)
            ]

            return RawCalculationResult(
                gi_t_h=self.g_parts[:self.geo.count_parts],
                pi_in_mpa=self.thermo.p_in_mpa[:self.geo.count_parts],
                ti_c=self.t_parts[:self.geo.count_parts],
                hi_kj_kg=self.h_parts[:self.geo.count_parts],
                dea_g=dea_g,
                dea_t=dea_t,
                dea_h=dea_h,
                dea_p_mpa=dea_p,
                ej_results=ej_results
            )
        except PhysicsEngineError:
            raise
        except Exception as e:
            logger.exception("Ошибка во время расчёта физики")
            raise PhysicsEngineError(f"Ошибка в расчётах: {e}")

    # --------------------------- Расчёты по участкам --------------------------- #
    def calculate_area1(self) -> None:
        self.h_parts[0] = self.thermo.h_start_kj_kg
        self.v_parts[0] = ph2v(self.thermo.p_in_mpa[0], self.h_parts[0])
        self.t_parts[0] = ph2t(self.thermo.p_in_mpa[0], self.h_parts[0])
        self.din_vis_parts[0] = ph(self.thermo.p_in_mpa[0], self.h_parts[0], 24)

        self.g_parts[0] = _part_props_detection(
            self.thermo.p_in_mpa[0], self.thermo.p_in_mpa[1],
            self.v_parts[0], self.din_vis_parts[0],
            self.geo.len_parts_m[0], self.geo.clearance_m, self.S, self.KSI,
        )

    def calculate_area2(self) -> None:
        if self.geo.count_parts < 2: return
        idx = _suction_index_for_area(self.geo.count_parts, 2)
        self.p_ejector = self.thermo.p_suctions_mpa[idx]

        if self.geo.count_parts > 2:
            self.h_parts[1] = self.thermo.h_start_kj_kg
            self.v_parts[1] = ph(self.thermo.p_in_mpa[1], self.h_parts[1], 3)
            self.t_parts[1] = ph(self.thermo.p_in_mpa[1], self.h_parts[1], 1)
            self.din_vis_parts[1] = ph(self.thermo.p_in_mpa[1], self.h_parts[1], 24)
            self.g_parts[1] = _part_props_detection(
                self.thermo.p_in_mpa[1], self.p_ejector,
                self.v_parts[1], self.din_vis_parts[1],
                self.geo.len_parts_m[1], self.geo.clearance_m, self.S, self.KSI,
            )
        else:
            self.h_parts[0] = self.thermo.h_start_kj_kg
            self.v_parts[0] = ph2v(self.thermo.p_in_mpa[0], self.h_parts[0])
            self.t_parts[0] = ph2t(self.thermo.p_in_mpa[0], self.h_parts[0])
            self.din_vis_parts[0] = ph(self.thermo.p_in_mpa[0], self.h_parts[0], 24)
            self.g_parts[0] = _part_props_detection(
                self.thermo.p_in_mpa[0], self.p_ejector,
                self.v_parts[0], self.din_vis_parts[0],
                self.geo.len_parts_m[0], self.geo.clearance_m, self.S, self.KSI,
            )

            self.h_parts[1] = self.h_air
            self.t_parts[1] = self.thermo.t_air_c
            self.v_parts[1] = air_calc(self.t_parts[1], 1)
            self.din_vis_parts[1] = air_calc(self.t_parts[1], 2)
            self.g_parts[1] = _part_props_detection(
                0.1013, self.p_ejector,
                self.v_parts[1], self.din_vis_parts[1],
                self.geo.len_parts_m[1], self.geo.clearance_m, self.S, self.KSI,
                last_part=True,
            )

    def calculate_area3(self) -> None:
        if self.geo.count_parts < 3: return
        idx = _suction_index_for_area(self.geo.count_parts, 3)
        self.p_ejector = self.thermo.p_suctions_mpa[idx]

        if self.geo.count_parts > 3:
            self.h_parts[2] = self.thermo.h_start_kj_kg
            self.v_parts[2] = ph(self.thermo.p_in_mpa[2], self.h_parts[2], 3)
            self.t_parts[2] = ph(self.thermo.p_in_mpa[2], self.h_parts[2], 1)
            self.din_vis_parts[2] = ph(self.thermo.p_in_mpa[2], self.h_parts[2], 24)
            self.g_parts[2] = _part_props_detection(
                self.thermo.p_in_mpa[2], self.p_ejector,
                self.v_parts[2], self.din_vis_parts[2],
                self.geo.len_parts_m[2], self.geo.clearance_m, self.S, self.KSI,
            )
        else:
            self.h_parts[2] = self.h_air
            self.t_parts[2] = self.thermo.t_air_c
            self.v_parts[2] = air_calc(self.t_parts[2], 1)
            self.din_vis_parts[2] = air_calc(self.t_parts[2], 2)
            self.g_parts[2] = _part_props_detection(
                0.1013, self.p_ejector,
                self.v_parts[2], self.din_vis_parts[2],
                self.geo.len_parts_m[2], self.geo.clearance_m, self.S, self.KSI,
                last_part=True,
            )

    def calculate_area4(self) -> None:
        if self.geo.count_parts < 4: return
        idx = _suction_index_for_area(self.geo.count_parts, 4)
        self.p_ejector = self.thermo.p_suctions_mpa[idx]

        if self.geo.count_parts > 4:
            self.h_parts[3] = self.thermo.h_start_kj_kg
            self.v_parts[3] = ph(self.thermo.p_in_mpa[3], self.h_parts[3], 3)
            self.t_parts[3] = ph(self.thermo.p_in_mpa[3], self.h_parts[3], 1)
            self.din_vis_parts[3] = ph(self.thermo.p_in_mpa[3], self.h_parts[3], 24)
            self.g_parts[3] = _part_props_detection(
                self.thermo.p_in_mpa[3], self.p_ejector,
                self.v_parts[3], self.din_vis_parts[3],
                self.geo.len_parts_m[3], self.geo.clearance_m, self.S, self.KSI,
            )
        else:
            self.h_parts[3] = self.h_air
            self.t_parts[3] = self.thermo.t_air_c
            self.v_parts[3] = air_calc(self.t_parts[3], 1)
            self.din_vis_parts[3] = air_calc(self.t_parts[3], 2)
            self.g_parts[3] = _part_props_detection(
                0.1013, self.p_ejector,
                self.v_parts[3], self.din_vis_parts[3],
                self.geo.len_parts_m[3], self.geo.clearance_m, self.S, self.KSI,
                last_part=True,
            )

    def calculate_area5(self) -> None:
        if self.geo.count_parts < 5: return
        idx = _suction_index_for_area(self.geo.count_parts, 5)
        self.p_ejector = self.thermo.p_suctions_mpa[idx]

        self.h_parts[4] = self.h_air
        self.t_parts[4] = self.thermo.t_air_c
        self.v_parts[4] = air_calc(self.t_parts[4], 1)
        self.din_vis_parts[4] = air_calc(self.t_parts[4], 2)
        self.g_parts[4] = _part_props_detection(
            0.1013, self.p_ejector,
            self.v_parts[4], self.din_vis_parts[4],
            self.geo.len_parts_m[4], self.geo.clearance_m, self.S, self.KSI,
            last_part=True,
        )

    # --------------------------- Отсосы --------------------------- #
    def deaerator_options(self) -> tuple[float, float, float, float]:
        if self.geo.count_parts < 2: return 0.0, 0.0, 0.0, 0.0
        h_dea, p_dea = self.h_parts[1], self.p_deaerator

        if self.geo.count_parts == 2: return 0.0, 0.0, h_dea, p_dea

        cv = self.thermo.count_valves
        if self.geo.count_parts == 3: g = (self.g_parts[0] - self.g_parts[1]) * cv
        elif self.geo.count_parts == 4: g = (self.g_parts[0] - self.g_parts[1] - self.g_parts[2]) * cv
        elif self.geo.count_parts == 5: g = (self.g_parts[0] - self.g_parts[1] - self.g_parts[2] - self.g_parts[3]) * cv
        else: raise PhysicsEngineError("Неверное количество участков.")

        t_dea = ph(p_dea, h_dea, 1)
        # Обрати внимание: мы больше не делим на 0.0980665! Ядро возвращает МПа.
        return g, t_dea, h_dea, p_dea

    def ejector_options(self) -> tuple[list[float], list[float], list[float], list[float]]:
        n = _expected_suctions(self.geo.count_parts)
        g_list, t_list, h_list, p_list = [0.0]*n, [0.0]*n, [0.0]*n, [0.0]*n

        if n == 0: return g_list, t_list, h_list, p_list

        cv = self.thermo.count_valves
        if self.geo.count_parts == 2:
            den = max(self.g_parts[1] + self.g_parts[0], 1e-9)
            g_list[0] = (self.g_parts[1] + self.g_parts[0]) * cv
            h_list[0] = (self.h_parts[1] * self.g_parts[1] + self.h_parts[0] * self.g_parts[0]) / den
            p_list[0] = self.thermo.p_suctions_mpa[0]
            t_list[0] = ph(p_list[0], h_list[0], 1)

        elif self.geo.count_parts == 3:
            den = max(self.g_parts[2] + self.g_parts[1], 1e-9)
            g_list[0] = (self.g_parts[2] + self.g_parts[1]) * cv
            h_list[0] = (self.h_parts[2] * 4.1868 * self.g_parts[2] + self.h_parts[1] * self.g_parts[1]) / den
            p_list[0] = self.thermo.p_suctions_mpa[0]
            t_list[0] = ph(p_list[0], h_list[0], 1)

        elif self.geo.count_parts == 4:
            g1 = max(self.g_parts[1] - self.g_parts[2] - self.g_parts[3], 0.0) * cv
            h1, p1 = self.h_parts[1], self.thermo.p_suctions_mpa[0]
            t1 = ph(p1, h1, 1)

            den2 = max(self.g_parts[3] + self.g_parts[2], 1e-9)
            g2 = abs(self.g_parts[2] - self.g_parts[3]) * cv
            h2 = (self.h_parts[3] * self.g_parts[3] + self.h_parts[2] * self.g_parts[2]) / den2
            p2 = self.thermo.p_suctions_mpa[1]
            t2 = ph(p2, h2, 1)
            g_list[:2], h_list[:2], p_list[:2], t_list[:2] = [g1, g2], [h1, h2], [p1, p2], [t1, t2]

        elif self.geo.count_parts == 5:
            g1 = max(self.g_parts[1] - self.g_parts[2] - self.g_parts[3], 0.0) * cv
            h1, p1 = self.h_parts[1], self.thermo.p_suctions_mpa[0]
            t1 = ph(p1, h1, 1)

            g2 = abs(self.g_parts[2] - self.g_parts[3]) * cv
            h2, p2 = self.h_parts[1], self.thermo.p_suctions_mpa[1]
            t2 = ph(p2, h2, 1)

            den3 = max(self.g_parts[4] + self.g_parts[3], 1e-9)
            g3 = (self.g_parts[3] + self.g_parts[4]) * cv
            h3 = (self.h_parts[4] * self.g_parts[4] + self.h_parts[3] * self.g_parts[3]) / den3
            p3 = self.thermo.p_suctions_mpa[2]
            t3 = ph(p3, h3, 1)
            g_list[:3], h_list[:3], p_list[:3], t_list[:3] = [g1, g2, g3], [h1, h2, h3], [p1, p2, p3], [t1, t2, t3]

        return g_list, t_list, h_list, p_list
