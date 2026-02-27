from dataclasses import dataclass

@dataclass(frozen=True)
class ValveGeometry:
    """
    Физическая геометрия клапана. 
    Никаких миллиметров! Все линейные размеры строго в МЕТРАХ.
    """
    count_parts: int
    diameter_m: float
    clearance_m: float
    radius_rounding_m: float
    len_parts_m: list[float]


@dataclass(frozen=True)
class ThermoConditions:
    """
    Начальные термодинамические условия расчёта.
    Единицы измерения строго зафиксированы в СИ / инженерной базе IF97:
    Давление - МПа, Температура - °C, Энтальпия - кДж/кг.
    """
    count_valves: int
    p_in_mpa: list[float]         # Давления перед каждым участком
    t_start_c: float              # Температура свежего пара
    h_start_kj_kg: float          # Энтальпия свежего пара
    t_air_c: float                # Температура окружающего воздуха
    p_suctions_mpa: list[float]   # Давления отсосов эжектора


@dataclass
class RawCalculationResult:
    """
    Сырой ответ физического движка (до конвертации обратно для UI).
    Расходы в т/ч, давления в МПа, температуры в °C, энтальпия в кДж/кг.
    """
    gi_t_h: list[float]
    pi_in_mpa: list[float]
    ti_c: list[float]
    hi_kj_kg: list[float]
    
    # Данные отсоса в деаэратор
    dea_g: float
    dea_t: float
    dea_h: float
    dea_p_mpa: float
    
    # Данные отсосов в эжектор(ы). 
    # Ожидаемый формат каждого элемента: {"g": ..., "t": ..., "h": ..., "p_mpa": ...}
    ej_results: list[dict[str, float]]