"""
Универсальный и расширяемый конвертер инженерных единиц измерения
(ориентирован на термодинамику, но не ограничивается ею).
"""

from __future__ import annotations
from typing import Callable, Union, Dict, Any

Number = Union[int, float]
FactorOrFunc = Union[Number, Callable[[Number], Number]]


class UnknownParameterError(ValueError):
    pass


class UnknownUnitError(ValueError):
    pass


def _linear(to_base_factor: float) -> tuple[Callable[[Number], Number],
                                            Callable[[Number], Number]]:
    """
    Вспомогательная фабрика. Возвращает две функции:
        - `to_base(value)`   : value * to_base_factor
        - `from_base(value)` : value / to_base_factor
    """
    return (
        lambda v, f=to_base_factor: v * f,
        lambda v, f=to_base_factor: v / f,
    )


class UnitConverter:
    """
    Главный класс-конвертер.

    Содержит словарь `self.parameters`, где каждая запись описывает один
    физический параметр (pressure, temperature, ...).

    Структура self.parameters
    -------------------------
    {
        'pressure': {
            'name': 'Давление',
            'base': 'кгс/см²',                # базовая единица (символ)
            'units': {
                'кгс/см²': {
                    'name': 'килограмм-сила на квадратный сантиметр',
                    'to_base': (lambda v: v),        # identity
                    'from_base': (lambda v: v)
                },
                'Па':  {
                    'name': 'паскаль',
                    'to_base':  lambda v: v / 98_066.5,
                    'from_base':lambda v: v * 98_066.5,
                },
                ...
            }
        },
        ...
    }
    """

    # -------------------------------------------------------------
    # API
    # -------------------------------------------------------------
    def __init__(self) -> None:
        self.parameters: Dict[str, Dict[str, Any]] = {}
        self._build_defaults()

    # ------------------------ PUBLIC -----------------------------
    def convert(self, value: Number, *,
                from_unit: str,
                to_unit: str,
                parameter_type: str) -> float:
        """
        Универсальная конвертация между двумя единицами
        одного параметра (pressure, temperature, ...).
        """
        parameter_type = self._norm_param(parameter_type)
        base_val = self.to_base(value, from_unit=from_unit,
                                parameter_type=parameter_type)
        return self.from_base(base_val, to_unit=to_unit,
                              parameter_type=parameter_type)

    def to_base(self, value: Number, *,
                from_unit: str,
                parameter_type: str) -> float:
        """Перевод `value` из `from_unit` → базовая единица параметра."""
        parameter_type = self._norm_param(parameter_type)
        unit = self._get_unit(parameter_type, from_unit)
        return unit["to_base"](value)

    def from_base(self, value: Number, *,
                  to_unit: str,
                  parameter_type: str) -> float:
        """Перевод `value` из базовой единицы параметра → `to_unit`."""
        parameter_type = self._norm_param(parameter_type)
        unit = self._get_unit(parameter_type, to_unit)
        return unit["from_base"](value)

    def get_available_units(self, parameter_type: str) -> list[str]:
        """Список всех поддерживаемых единиц (символы)."""
        parameter_type = self._norm_param(parameter_type)
        return list(self.parameters[parameter_type]["units"])

    def get_base_unit(self, parameter_type: str) -> str:
        """Символ базовой единицы параметра."""
        parameter_type = self._norm_param(parameter_type)
        return self.parameters[parameter_type]["base"]

    # ------ Расширение (динамическое добавление) -----------------
    def add_parameter(self,
                      parameter_type: str,
                      *,
                      base_unit_symbol: str,
                      base_unit_name: str) -> None:
        """Добавить новый тип физического параметра."""
        p = self._norm_param(parameter_type)
        if p in self.parameters:
            raise ValueError(f"Parameter '{parameter_type}' уже существует")
        self.parameters[p] = {
            "name": parameter_type,
            "base": base_unit_symbol,
            "units": {
                base_unit_symbol: {
                    "name": base_unit_name,
                    "to_base": lambda v: v,   # identity
                    "from_base": lambda v: v,
                }
            },
        }

    def add_unit(self,
                 parameter_type: str,
                 *,
                 unit_symbol: str,
                 unit_name: str,
                 to_base: FactorOrFunc,
                 from_base: FactorOrFunc | None = None) -> None:
        """
        Добавить новую единицу к существующему параметру.

        Если `to_base` и/или `from_base` — число,
        то считаем это линейным коэффициентом.
        """
        parameter_type = self._norm_param(parameter_type)
        if parameter_type not in self.parameters:
            raise UnknownParameterError(parameter_type)

        # Превращаем фактор в функцию (если нужно)
        if not callable(to_base):
            to_base_func = lambda v, f=float(to_base): v * f
        else:
            to_base_func = to_base

        if from_base is None:
            # для линейного случая достаточно обратного коэффициента
            if callable(to_base):
                raise ValueError("from_base обязателен для нелинейных "
                                 "конверсий")
            else:
                from_base = 1 / float(to_base)

        if not callable(from_base):
            from_base_func = lambda v, f=float(from_base): v * f
        else:
            from_base_func = from_base

        self.parameters[parameter_type]["units"][unit_symbol] = {
            "name": unit_name,
            "to_base": to_base_func,
            "from_base": from_base_func,
        }

    # ---------------------- INTERNAL -----------------------------
    # нормализация ключа параметра
    @staticmethod
    def _norm_param(p: str) -> str:
        return p.strip().lower()

    def _get_unit(self, parameter_type: str, unit_symbol: str) -> Dict[str, Any]:
        if parameter_type not in self.parameters:
            raise UnknownParameterError(parameter_type)

        units_dict = self.parameters[parameter_type]["units"]
        if unit_symbol not in units_dict:
            raise UnknownUnitError(
                f"Unit '{unit_symbol}' is not registered for parameter "
                f"'{parameter_type}'."
            )
        return units_dict[unit_symbol]

    # ------------------- Default parameters ----------------------
    def _build_defaults(self) -> None:
        """Инициализация «из коробки»."""
        # 1) Pressure ------------------------------------------------
        self.add_parameter("pressure",
                           base_unit_symbol="кгс/см²",
                           base_unit_name="килограмм-сила на квадратный сантиметр")

        # линейные коэффициенты через фабрику _linear
        to_base, from_base = _linear(1.0)  # identity для примера
        # (базовая записана выше; повтор добавлять не нужно)

        # Па
        self.add_unit("pressure",
                      unit_symbol="Па",
                      unit_name="паскаль",
                      to_base=lambda v: v / 98_066.5,
                      from_base=lambda v: v * 98_066.5)

        # кПа
        self.add_unit("pressure",
                      unit_symbol="кПа",
                      unit_name="килопаскаль",
                      to_base=lambda v: v * 1_000 / 98_066.5,
                      from_base=lambda v: v * 98_066.5 / 1_000)

        # МПа
        self.add_unit("pressure",
                      unit_symbol="МПа",
                      unit_name="мегапаскаль",
                      to_base=lambda v: v * 1_000_000 / 98_066.5,
                      from_base=lambda v: v * 98_066.5 / 1_000_000)

        # бар
        self.add_unit("pressure",
                      unit_symbol="бар",
                      unit_name="бар",
                      to_base=lambda v: v * 100_000 / 98_066.5,
                      from_base=lambda v: v * 98_066.5 / 100_000)

        # атм
        self.add_unit("pressure",
                      unit_symbol="атм",
                      unit_name="атмосфера",
                      to_base=lambda v: v * 101_325 / 98_066.5,
                      from_base=lambda v: v * 98_066.5 / 101_325)

        # мм рт. ст.
        self.add_unit("pressure",
                      unit_symbol="мм рт. ст.",
                      unit_name="миллиметр ртутного столба",
                      to_base=lambda v: v * 133.322 / 98_066.5,
                      from_base=lambda v: v * 98_066.5 / 133.322)

        # 2) Temperature --------------------------------------------
        self.add_parameter("temperature",
                           base_unit_symbol="°C",
                           base_unit_name="градус Цельсия")

        # Kelvin
        self.add_unit("temperature",
                      unit_symbol="K",
                      unit_name="кельвин",
                      to_base=lambda v: v - 273.15,        # K -> °C
                      from_base=lambda v: v + 273.15)      # °C -> K

        # 3) Enthalpy -----------------------------------------------
        self.add_parameter("enthalpy",
                           base_unit_symbol="ккал/кг",
                           base_unit_name="килокалория на килограмм")

        kJ_coeff = 1 / 4.1868  # кДж/кг -> ккал/кг
        self.add_unit("enthalpy",
                      unit_symbol="кДж/кг",
                      unit_name="килоджоуль на килограмм",
                      to_base=lambda v, c=kJ_coeff: v * c,
                      from_base=lambda v, c=kJ_coeff: v / c)

        J_coeff = 1 / 4186.8
        self.add_unit("enthalpy",
                      unit_symbol="Дж/кг",
                      unit_name="джоуль на килограмм",
                      to_base=lambda v, c=J_coeff: v * c,
                      from_base=lambda v, c=J_coeff: v / c)

        # 4) Entropy -------------------------------------------------
        self.add_parameter("entropy",
                           base_unit_symbol="ккал/кгК",
                           base_unit_name="килокалория на килограмм-кельвин")

        kJ_coeff_S = 1 / 4.1868
        self.add_unit("entropy",
                      unit_symbol="кДж/кгК",
                      unit_name="килоджоуль на килограмм-кельвин",
                      to_base=lambda v, c=kJ_coeff_S: v * c,
                      from_base=lambda v, c=kJ_coeff_S: v / c)

        # 5) Density -------------------------------------------------
        self.add_parameter("density",
                           base_unit_symbol="кг/м³",
                           base_unit_name="килограмм на кубический метр")

        # Пример других единиц (г/см³) — покажем как фактор:
        g_cm3_factor = 1000  # 1 г/см³ = 1000 кг/м³
        self.add_unit("density",
                      unit_symbol="г/см³",
                      unit_name="грамм на кубический сантиметр",
                      to_base=g_cm3_factor,
                      from_base=1 / g_cm3_factor)

        # 6) Specific volume ----------------------------------------
        self.add_parameter("specific_volume",
                           base_unit_symbol="м³/кг",
                           base_unit_name="кубический метр на килограмм")
        # (для краткости доп. ед. не добавляем)

        # 7) Power ---------------------------------------------------
        self.add_parameter("power",
                           base_unit_symbol="МВт",
                           base_unit_name="мегаватт")

        self.add_unit("power",
                      unit_symbol="кВт",
                      unit_name="киловатт",
                      to_base=0.001,
                      from_base=1000)

        self.add_unit("power",
                      unit_symbol="Вт",
                      unit_name="ватт",
                      to_base=0.000001,
                      from_base=1_000_000)

        hp_factor = 0.00073549875
        self.add_unit("power",
                      unit_symbol="л.с.",
                      unit_name="метрическая лошадиная сила",
                      to_base=hp_factor,
                      from_base=1 / hp_factor)

        # 8) Mass flow rate -----------------------------------------
        self.add_parameter("mass_flow",
                           base_unit_symbol="т/ч",
                           base_unit_name="тонна в час")

        self.add_unit("mass_flow",
                      unit_symbol="кг/с",
                      unit_name="килограмм в секунду",
                      to_base=3.6,          # 1 кг/с = 3.6 т/ч
                      from_base=1 / 3.6)

        self.add_unit("mass_flow",
                      unit_symbol="кг/ч",
                      unit_name="килограмм в час",
                      to_base=0.001,        # 1 кг/ч = 0.001 т/ч
                      from_base=1000)

        # 9) Heat power (Q) -----------------------------------------
        self.add_parameter("heat_power",
                           base_unit_symbol="Гкал/ч",
                           base_unit_name="гигакалория в час")

        # МДж/ч
        mjh_coeff = 1 / (4.1868 * 1000)  # 1 МДж/ч -> Гкал/ч
        self.add_unit("heat_power",
                      unit_symbol="МДж/ч",
                      unit_name="мегаджоуль в час",
                      to_base=mjh_coeff,
                      from_base=1 / mjh_coeff)

        # кВт
        kw_coeff = 3600 / (4.1868e9)  # 1 кВт = 1 kJ/s = 3600 kJ/h
        self.add_unit("heat_power",
                      unit_symbol="кВт",
                      unit_name="киловатт (тепловая мощность)",
                      to_base=kw_coeff,
                      from_base=1 / kw_coeff)

        # 10) Dryness / Moisture fraction ---------------------------
        self.add_parameter("quality",
                           base_unit_symbol="fraction",
                           base_unit_name="доля (0–1)")

        self.add_unit("quality",
                      unit_symbol="%",
                      unit_name="проценты",
                      to_base=lambda v: v / 100.0,
                      from_base=lambda v: v * 100.0)

    # -------------------------------------------------------------


# -----------------------------------------------------------------
# Пример использования
# -----------------------------------------------------------------
if __name__ == "__main__":
    uc = UnitConverter()

    # 1. Давление: 10 бар → кгс/см²
    p_kgf = uc.convert(10, from_unit="бар", to_unit="кгс/см²",
                       parameter_type="pressure")
    print(f"10 бар = {p_kgf:.3f} кгс/см²")

    # 2. Температура: 100 °C → K
    t_kelvin = uc.convert(100, from_unit="°C", to_unit="K",
                          parameter_type="temperature")
    print(f"100 °C = {t_kelvin:.2f} K")

    # 3. Плотность: 1.2 г/см³ → кг/м³
    rho = uc.convert(1.2, from_unit="г/см³", to_unit="кг/м³",
                     parameter_type="density")
    print(f"1.2 г/см³ = {rho:.1f} кг/м³")

    # 4. Качество (dryness) 85 % → доля
    x_fraction = uc.to_base(85, from_unit="%", parameter_type="quality")
    print(f"85 % = {x_fraction:.3f} (доля)")

    # 5. Мощность 2500 кВт → л.с.
    hp = uc.convert(2500, from_unit="кВт", to_unit="л.с.",
                    parameter_type="power")
    print(f"2500 кВт = {hp:.1f} л.с.")

    # Список доступных единиц для давления
    print("Доступные единицы давления:", uc.get_available_units("pressure"))