from _common import setup_path


setup_path()

import pandas as pd

from app.utils.VKU_strategy import VKUStrategy


def run_validation():
    """
    Скрипт для валидации класса VKUStrategy на предоставленном наборе данных.
    """
    print("--- Запуск валидации расчета ВКУ (интерфейс на словарях) ---")

    mass_flow_nom = 1250.0
    dryness_nom = 0.92
    temperature_air = 20.0
    print(f"Используются номинальные параметры: Gном = {mass_flow_nom} т/ч, Xном = {dryness_nom}")
    print(f"Используется температура наружного воздуха (tвозд): {temperature_air}°С\n")

    strategy = VKUStrategy(mass_flow_steam_nom=mass_flow_nom, degree_dryness_steam_nom=dryness_nom)

    validation_data = {
        "G": [301.2, 296.8, 291.4, 247.8, 245.1, 241.5, 186.5, 186.1, 185.3, 282.72, 277.9, 311.5, 305.9, 307.8],
        "X": [0.903, 0.907, 0.914, 0.908, 0.914, 0.921, 0.907, 0.915, 0.924, 0.91, 0.914, 0.904, 0.91, 0.909],
        "P_expected": [
            0.091366573,
            0.13082959,
            0.162134878,
            0.077804347,
            0.112168783,
            0.139803093,
            0.067811128,
            0.098300643,
            0.122569889,
            0.134806483,
            0.146941106,
            0.126750725,
            0.157444183,
            0.156322495,
        ],
    }
    df = pd.DataFrame(validation_data, index=[f"Режим {i + 1}" for i in range(len(validation_data["G"]))])

    results_list = []
    for _, row in df.iterrows():
        input_params = {
            "mass_flow_flow_path_1": row["G"],
            "degree_dryness_flow_path_1": row["X"],
            "temperature_air": temperature_air,  # Используем единую температуру для всех
        }

        result_dict = strategy.calculate(input_params)
        results_list.append(result_dict)

    results_df = pd.DataFrame(results_list, index=df.index)
    df["G_reduced_calc [%]"] = results_df["mass_flow_reduced_steam_condencer"]
    df["P_calculated [кгс/см²]"] = results_df["pressure_flow_path_1"]

    df["Absolute_Error"] = abs(df["P_calculated [кгс/см²]"] - df["P_expected"])
    df["Relative_Error_%"] = (df["Absolute_Error"] / df["P_expected"]) * 100

    pd.options.display.float_format = "{:,.7f}".format
    pd.set_option("display.width", 120)

    print("Результаты валидации:")
    print(df[["G", "X", "P_expected", "P_calculated [кгс/см²]", "Relative_Error_%"]])

    max_rel_error = df["Relative_Error_%"].max()
    print(f"\nМаксимальная относительная погрешность: {max_rel_error:.4f}%")

    if max_rel_error > 5.0:  # Порог для предупреждения
        print(
            "\nРезультат: ВНИМАНИЕ! Высокая погрешность в некоторых режимах (возможно, неверно заданы t° воздуха или Gном/Xном)."
        )
    else:
        print("\nРезультат: ВАЛИДАЦИЯ ПРОЙДЕНА УСПЕШНО.")


if __name__ == "__main__":
    run_validation()

