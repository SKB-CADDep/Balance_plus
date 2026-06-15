"""
Скрипт профилирования и сравнения математических решателей (Solvers).

Запускает бенчмаркинг реализованных численных и аналитических методов,
используемых для подбора параметров (нахождения корней уравнений) в ядре 
калькулятора конденсаторов. Оценивает скорость сходимости, точность
и затрачиваемое процессорное время.
"""

from _common import setup_path

setup_path()

import time

from app.utils.base_for_selection import ProblemDefinition
from app.utils.selection_methods import AnalyticalSolver, BisectionSolver, NewtonSolver


def run_comparison() -> list[dict]:
    """
    Запускает все реализованные решатели и собирает метрики их работы.

    Выполняет множественный прогон (бенчмарк) каждого метода для получения 
    статистически значимого времени выполнения, исключая влияние планировщика ОС.

    Returns:
        list[dict]: Список словарей с результатами работы каждого метода.
            Каждый словарь содержит ключи: 'Метод', 'Найденный X', 'Итераций',
            'Время (μs/запуск)', 'Итоговый A3_delt'.
    """
    problem = ProblemDefinition()
    target_accuracy = 0.001

    # [ENGINEERING CONTEXT]
    # Разница в параметрах обусловлена математической природой алгоритмов:
    # - Дихотомия (Bisection) — это "bracket method", требующий указания закрытого 
    #   интервала [a, b], на концах которого функция имеет разные знаки.
    # - Метод Ньютона (Newton-Raphson) — это "open method", требующий лишь одной 
    #   начальной точки приближения (initial_guess) и опирающийся на касательные (производные).
    solver_params = {
        "Аналитический": {},
        "Метод Дихотомии": {"a": 1.0, "b": 5.0},
        "Метод Ньютона": {"initial_guess": 2.0},
    }

    solvers = {
        "Аналитический": AnalyticalSolver(problem),
        "Метод Дихотомии": BisectionSolver(problem),
        "Метод Ньютона": NewtonSolver(problem),
    }

    results = []
    
    # [ENGINEERING CONTEXT]
    # Почему N_RUNS = 1000: Время выполнения одного прогона численного метода может 
    # составлять единицы микросекунд. Замер одного прогона будет сильно искажен 
    # погрешностью системного таймера и прерываниями ОС. 1000 прогонов позволяют 
    # сгладить эту погрешность и получить точное среднее время на 1 запуск.
    N_RUNS = 1000

    for name, solver in solvers.items():
        try:
            params = solver_params[name]

            # Используется time.perf_counter(), так как это аппаратный счетчик 
            # с наивысшим доступным разрешением (в отличие от обычного time.time()), 
            # что критически важно для профилирования математики.
            start_time = time.perf_counter()
            found_x = 0
            for _ in range(N_RUNS):
                found_x = solver.solve(target_delta=target_accuracy, **params)
            end_time = time.perf_counter()

            duration_us = (end_time - start_time) * 1e6 / N_RUNS
            final_delta = problem.calculate_delta(found_x)

            results.append(
                {
                    "Метод": name,
                    "Найденный X": found_x,
                    "Итераций": solver.iterations,
                    "Время (μs/запуск)": duration_us,
                    "Итоговый A3_delt": final_delta,
                }
            )
        except (RuntimeError, ValueError) as e:
            results.append(
                {
                    "Метод": name,
                    "Найденный X": "Ошибка",
                    "Итераций": solver.iterations,
                    "Время (μs/запуск)": "N/A",
                    "Итоговый A3_delt": str(e),
                }
            )

    return results


def print_results_to_console(results: list[dict]) -> None:
    """
    Выводит результаты бенчмарка в консоль в виде форматированной ASCII-таблицы.

    Args:
        results (list[dict]): Список результатов, сгенерированный функцией run_comparison().
    """
    print("Цель: подобрать X, чтобы A3_delt был равен 0.001")
    print("-" * 80)
    print(
        f"{'Метод':<20} | {'Найденный X':<18} | {'Итераций':<10} | {'Время (μs/запуск)':<20} | {'Итоговый A3_delt':<20}"
    )
    print("=" * 100)
    for res in results:
        x_str = f"{res['Найденный X']:.8f}" if isinstance(res["Найденный X"], float) else str(res["Найденный X"])
        t_str = (
            f"{res['Время (μs/запуск)']:.4f}"
            if isinstance(res["Время (μs/запуск)"], float)
            else str(res["Время (μs/запуск)"])
        )
        d_str = (
            f"{res['Итоговый A3_delt']:.10f}"
            if isinstance(res["Итоговый A3_delt"], float)
            else str(res["Итоговый A3_delt"])
        )

        print(f"{res['Метод']:<20} | {x_str:<18} | {res['Итераций']:<10} | {t_str:<20} | {d_str:<20}")


if __name__ == "__main__":
    comparison_results = run_comparison()
    print_results_to_console(comparison_results)
    