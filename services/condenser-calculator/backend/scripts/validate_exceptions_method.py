from _common import setup_path
setup_path()

from app.utils.exceptions_method import CondenserExceptions


def report_condenser_pressure(
    pressure_condenser: float | None,
    temperature_cooling_water_1: float | None,
    pif: float | None,
):
    """
    Создает отчет по расчету давления P1 для участка конденсатора.

    Эта функция отвечает за:
    1. Создание экземпляра калькулятора CondenserExceptions.
    2. Вызов метода расчета.
    3. Форматирование и вывод результатов для пользователя и разработчика.
    """
    print("--- Новый расчет ---")
    print(
        "Входные данные:\n"
        f"  Pк (pressure_condenser) = {pressure_condenser}\n"
        f"  tов1 (temperature_cooling_water_1) = {temperature_cooling_water_1}\n"
        f"  PIF = {pif}"
    )

    calculator = CondenserExceptions(
        pressure_condenser=pressure_condenser,
        temperature_cooling_water_1=temperature_cooling_water_1,
        pif=pif,
    )

    result = calculator.calculate_pressure()

    print("\nРезультаты:")
    if result is not None:
        print("  Расчет выполнен успешно.")
        print(f"  Вывод для пользователя: P1 = {result}")
        print(f"  Вывод для разработчика: pressure_flow_path_1 = {calculator.pressure_flow_path_1}")
    else:
        print("  Ни одно из условий методологии не выполнено. Результат не определен.")

    print("-" * 20 + "\n")


if __name__ == "__main__":
    print(">>> Тестируем Случай 1: Pк задано")
    report_condenser_pressure(
        pressure_condenser=0.04,
        temperature_cooling_water_1=15.0,
        pif=0.05,
    )

    print(">>> Тестируем Случай 2: Pк и tов1 не заданы, используется PIF")
    report_condenser_pressure(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=0.05,
    )

    print(">>> Тестируем Случай 3: Условия не выполнены (Pк не задан, но tов1 задана)")
    report_condenser_pressure(
        pressure_condenser=None,
        temperature_cooling_water_1=18.0,
        pif=0.05,
    )

    print(">>> Тестируем Случай 4: Условия не выполнены (все входные данные None)")
    report_condenser_pressure(
        pressure_condenser=None,
        temperature_cooling_water_1=None,
        pif=None,
    )

