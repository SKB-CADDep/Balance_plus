"""
Скрипт профилирования и валидации табличного метода расчета давления (TPS).

Этот модуль демонстрирует работу `TablePressureStrategy`, которая вычисляет 
давление отработавшего пара в конденсаторе на основе эмпирических (заводских) 
нормативных характеристик. Включает примеры билинейной 2D-интерполяции 
и линейной 1D-интерполяции.
"""

from _common import setup_path

setup_path()

from pprint import pprint

from app.utils.TPS_module import TablePressureStrategy

# [ENGINEERING CONTEXT]
# Что такое NAMET и NAMED: 
# Это исторические названия массивов данных (вероятно, унаследованные из старых программ на Fortran).
# - NAMET: 2D-матрица нормативной характеристики конденсатора. Описывает зависимость давления 
#   от температуры охлаждающей воды (t_ов1) и массового расхода пара (G_к).
# - NAMED: 1D-кривая предельного (минимально достижимого) давления. Она определяется 
#   характеристикой воздухоудаляющего устройства (эжектора) или плотностью вакуумной системы.
params = {
    "NAMET": {
        "data": [
            [35, 33, 30, 25],
            [20, 50, 100, 150, 200],
            [
                [6.549, 7.211, 8.88, 10.945, 13.409],
                [5.9, 6.499, 8.018, 9.927, 12.214],
                [5.036, 5.552, 6.872, 8.572, 10.622],
                [3.851, 4.257, 5.299, 6.712, 8.438],
            ],
        ],
    },
    "NAMED": {
        "data": [
            [15.3, 26.8, 38.4, 49.9, 61.5, 73],
            [0.157, 0.258, 0.469, 0.607, 0.763, 0.919],
        ],
    },
    "inputs": {
        "temperature_cooling_water_1": 30.0,
        "mass_flow_flow_path_1": 112.0,
    },
}


if __name__ == "__main__":
    strategy = TablePressureStrategy()

    print("=" * 20 + " Расчет давления в конденсаторе " + "=" * 20)
    print("Входные параметры:")
    pprint(params, indent=2)

    results = strategy.calculate(params)

    print("\n--- Промежуточные результаты ---")

    t_namet = params["inputs"]["temperature_cooling_water_1"]
    g_namet = params["inputs"]["mass_flow_flow_path_1"]
    t_named = params["inputs"]["temperature_cooling_water_1"]

    p_namet = results["pressure_flow_path_1_NAMET"]
    p_named = results["pressure_flow_path_1_NAMED"]

    print(f"Расчет по NAMET (tов1={t_namet}, G1={g_namet}):")
    print(f"  -> pressure_flow_path_1_NAMET = {p_namet:.4f}")

    print(f"Расчет по NAMED (tов1={t_named}):")
    print(f"  -> pressure_flow_path_1_NAMED = {p_named:.4f}")

    # [ENGINEERING CONTEXT]
    # Почему итоговое давление берется как максимум из двух значений:
    # Физика процесса такова, что конденсатор стремится создать глубокий вакуум (NAMET),
    # но давление физически не может опуститься ниже предела, который способен 
    # откачать эжектор (NAMED). Выбирая максимальное из двух давлений, алгоритм гарантирует, 
    # что расчет не выдаст физически невозможный (избыточно глубокий) вакуум.
    print("\n--- Итоговый результат ---")
    final_pressure = results["pressure_flow_path_1"]
    print(f"Итоговое давление pressure_flow_path_1 = max({p_namet:.4f}, {p_named:.4f}) = {final_pressure:.3f}")

    print("\n--- Сверка с ожидаемыми значениями ---")
    print(f"Ожидаемый P1(NAMET) при t=27, G=112: ~7.758, полученный: {p_namet:.3f}")
    print(f"Ожидаемый P1(NAMED) при t=30:        ~0.316, полученный: {p_named:.3f}")
    print(f"Ожидаемый итоговый P1:                7.758, полученный: {final_pressure:.3f}")
    