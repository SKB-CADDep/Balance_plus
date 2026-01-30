import math
from utils.base_for_selection import ProblemDefinition


class AnalyticalSolver:  # Аналитически!
    """Решает задачу аналитически. Максимальная скорость, но не универсален."""

    def __init__(self, problem: ProblemDefinition):
        self.problem = problem
        self.iterations = 0
        self._inv_power = 1.0 / problem.power_minus_1

    def solve(self, target_delta, **kwargs):
        self.iterations = 1  # Считается за одну операцию
        base = (1.0 - target_delta) / self.problem.c
        if base < 0:
            raise ValueError("Невозможно найти вещественное решение: основание степени отрицательное.")
        return math.pow(base, self._inv_power)


class BisectionSolver:  # Дихотомии!
    """Решает задачу методом дихотомии. Надежен, но медленнее сходится."""

    def __init__(self, problem: ProblemDefinition, max_iter=100, tol=1e-7):
        self.problem = problem
        self.max_iter = max_iter
        self.tol = tol
        self.iterations = 0

    def solve(self, target_delta, a=1.0, b=10.0):  # Начальный отрезок [1, 10]
        self.iterations = 0
        fa = self.problem.f(a, target_delta)
        fb = self.problem.f(b, target_delta)

        if fa * fb >= 0:
            raise ValueError("На концах отрезка [a,b] функция имеет одинаковый знак.")

        for i in range(self.max_iter):
            self.iterations += 1
            c = (a + b) / 2
            fc = self.problem.f(c, target_delta)

            if (b - a) / 2 < self.tol:
                return c

            if fa * fc < 0:
                b = c
            else:
                a = c
                fa = fc

        raise RuntimeError(f"Метод дихотомии не сошелся за {self.max_iter} итераций")


class NewtonSolver:  # Ньютоном!
    """Решает задачу методом Ньютона. Быстрая сходимость, но требует производную."""

    def __init__(self, problem: ProblemDefinition, max_iter=20, tol=1e-9):
        self.problem = problem
        self.max_iter = max_iter
        self.tol = tol
        self.iterations = 0

    def solve(self, target_delta, initial_guess=2.0):
        self.iterations = 0
        x = float(initial_guess)

        for i in range(self.max_iter):
            self.iterations += 1
            fx = self.problem.f(x, target_delta)

            if abs(fx) < self.tol:
                return x

            dfx = self.problem.df(x)
            if abs(dfx) < 1e-12:
                raise RuntimeError("Производная близка к нулю. Деление на ноль.")

            x = x - fx / dfx

        raise RuntimeError(f"Метод Ньютона не сошелся за {self.max_iter} итераций")
