from pprint import pprint
from app.utils.TPS_module import TablePressureStrategy

def run_validation_case(strategy: TablePressureStrategy, params: dict, title: str, tolerance_percent: float):
    """
    Выполняет один тестовый случай: запускает расчет, сравнивает с эталоном и печатает отчет.
    """
    print("=" * 25 + f" {title} " + "=" * 25)
    print("Входные параметры:")
    pprint(params, indent=2, width=100)

    calculated_results = strategy.calculate(params)
    calculated_value = calculated_results['pressure_flow_path_1']
    
    expected_value = params['inputs']['expected_pressure_flow_path_1']

    abs_diff = abs(calculated_value - expected_value)
    if expected_value != 0:
        percentage_diff = (abs_diff / abs(expected_value)) * 100
    else:
        percentage_diff = 0.0 if calculated_value == 0.0 else float('inf')
        
    is_converged = percentage_diff <= tolerance_percent
    status = "УСПЕХ" if is_converged else "ПРОВАЛ"

    print("\n--- Отчет по валидации ---")
    print(f"  Промежуточный P1(NAMET): {calculated_results['pressure_flow_path_1_NAMET']:.4f}")
    print(f"  Промежуточный P1(NAMED): {calculated_results['pressure_flow_path_1_NAMED']:.4f}")
    print("-" * 30)
    print(f"  Ожидаемый результат:   {expected_value:.4f}")
    print(f"  Рассчитанный результат: {calculated_value:.4f}")
    print(f"  Допустимое расхождение: {tolerance_percent:.2f}%")
    print(f"  Фактическое расхождение: {percentage_diff:.2f}%")
    print(f"  СТАТУС: {status}\n")


if __name__ == "__main__":
    NAMET_DATA = {'data': [[35, 33, 30, 25], [20, 50, 100, 150, 200], [[6.549, 7.211, 8.88, 10.945, 13.409], [5.9, 6.499, 8.018, 9.927, 12.214], [5.036, 5.552, 6.872, 8.572, 10.622], [3.851, 4.257, 5.299, 6.712, 8.438]]]}
    NAMED_DATA = {'data': [[15.3, 26.8, 38.4, 49.9, 61.5, 73], [0.157, 0.258, 0.469, 0.607, 0.763, 0.919]]}

    
    # Тест 1: ПРОВАЛЬНЫЙ. Сравниваем верный расчет (6.295) с неверным эталоном (7.758).
    params_fail = {
        'NAMET': NAMET_DATA, 'NAMED': NAMED_DATA,
        'inputs': {
            'temperature_cooling_water_1': 27.0,
            'mass_flow_flow_path_1': 112.0,
            'expected_pressure_flow_path_1': 7.758
        }
    }

    # Тест 2: УСПЕШНЫЙ. Сравниваем верный расчет (7.280) с верным эталоном.
    params_pass = {
        'NAMET': NAMET_DATA, 'NAMED': NAMED_DATA,
        'inputs': {
            'temperature_cooling_water_1': 30.0,
            'mass_flow_flow_path_1': 112.0,
            'expected_pressure_flow_path_1': 7.280
        }
    }
        
    calculation_strategy = TablePressureStrategy()
    
    run_validation_case(calculation_strategy, params_fail, "Тест 1: Неверный эталон", tolerance_percent=5.0)
    run_validation_case(calculation_strategy, params_pass, "Тест 2: Корректный эталон", tolerance_percent=1.0)