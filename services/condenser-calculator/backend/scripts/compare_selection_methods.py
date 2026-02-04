from _common import setup_path


setup_path()

import time

from app.utils.base_for_selection import ProblemDefinition
from app.utils.selection_methods import AnalyticalSolver, BisectionSolver, NewtonSolver


def run_comparison():
    """
    Запускает все реализованные решатели и возвращает результаты.
    """
    problem = ProblemDefinition()
    target_accuracy = 0.001

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
    N_RUNS = 1000

    for name, solver in solvers.items():
        try:
            params = solver_params[name]

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


def print_results_to_console(results):
    """Выводит результаты в консоль в виде таблицы."""
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
