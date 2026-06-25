"""
Библиотека численных и аналитических методов (решателей) для поиска корней.

Содержит реализации паттерна Стратегия для решения уравнения F(x) = 0,
где математическая модель инкапсулирована в объект `ProblemDefinition`.
Предоставляет выбор между аналитическим решением, методом дихотомии и методом Ньютона, 
позволяя балансировать между скоростью работы и надежностью сходимости.
"""

import math

from .base_for_selection import ProblemDefinition


class AnalyticalSolver:  # Аналитически!
    """
    Решает задачу аналитическим способом (прямое математическое обращение функции). 
    
    Обладает максимальной скоростью выполнения O(1), так как вычисляет корень 
    за одну математическую операцию. Однако метод не универсален и применим 
    только к функциям, которые можно обратить алгебраически.
    """

    def __init__(self, problem: ProblemDefinition):
        """
        Инициализирует аналитический решатель.

        Args:
            problem (ProblemDefinition): Объект, содержащий константы и параметры уравнения.
        """
        self.problem = problem
        self.iterations = 0
        self._inv_power = 1.0 / problem.power_minus_1

    def solve(self, target_delta, **kwargs):
        """
        Вычисляет точный корень уравнения напрямую.

        Args:
            target_delta (float): Целевое значение для расчета.
            **kwargs: Перехватывает дополнительные аргументы (например, a, b), 
                передаваемые другими методами, для сохранения единого интерфейса решателей.

        Returns:
            float: Точное значение найденного корня.

        Raises:
            ValueError: Если основание степени отрицательное (невозможно найти 
                вещественное решение в рамках действительных чисел).
        """
        self.iterations = 1  # Считается за одну операцию
        base = (1.0 - target_delta) / self.problem.c
        if base < 0:
            raise ValueError("Невозможно найти вещественное решение: основание степени отрицательное.")
        return math.pow(base, self._inv_power)


class BisectionSolver:  # Дихотомии!
    """
    Решает задачу методом половинного деления (дихотомии). 
    
    Отличается высокой надежностью: гарантированно сходится, если на концах 
    заданного отрезка функция имеет разные знаки. Работает медленнее градиентных 
    методов (логарифмическая сходимость).
    """

    def __init__(self, problem: ProblemDefinition, max_iter=100, tol=1e-7):
        """
        Инициализирует решатель методом дихотомии.

        Args:
            problem (ProblemDefinition): Объект целевой функции.
            max_iter (int): Максимально допустимое число итераций. По умолчанию 100.
            tol (float): Допустимая погрешность (точность). По умолчанию 1e-7.
        """
        self.problem = problem
        self.max_iter = max_iter
        self.tol = tol
        self.iterations = 0

    def solve(self, target_delta, a=1.0, b=10.0):  # Начальный отрезок [1, 10]
        """
        Итеративно сужает интервал поиска до достижения заданной точности.

        Args:
            target_delta (float): Целевое значение функции.
            a (float): Левая граница интервала поиска. По умолчанию 1.0.
            b (float): Правая граница интервала поиска. По умолчанию 10.0.

        Returns:
            float: Приближенное значение корня.

        Raises:
            ValueError: Если функция имеет одинаковый знак на концах отрезка 
                (корень не локализован).
            RuntimeError: Если алгоритм не сошелся за отведенное число итераций.
        """
        self.iterations = 0
        fa = self.problem.f(a, target_delta)
        fb = self.problem.f(b, target_delta)

        if fa * fb >= 0:
            raise ValueError("На концах отрезка [a,b] функция имеет одинаковый знак.")

        for _i in range(self.max_iter):
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
    """
    Решает задачу методом касательных (метод Ньютона-Рафсона). 
    
    Обеспечивает квадратичную скорость сходимости (очень быстро находит точный ответ), 
    но требует наличия первой производной целевой функции. Может не сойтись 
    при неудачном выборе начального приближения.
    """

    def __init__(self, problem: ProblemDefinition, max_iter=20, tol=1e-9):
        """
        Инициализирует решатель методом Ньютона.

        Args:
            problem (ProblemDefinition): Объект целевой функции (должен предоставлять методы `f` и `df`).
            max_iter (int): Максимально допустимое число итераций. По умолчанию 20.
            tol (float): Допустимая погрешность (точность). По умолчанию 1e-9.
        """
        self.problem = problem
        self.max_iter = max_iter
        self.tol = tol
        self.iterations = 0

    def solve(self, target_delta, initial_guess=2.0):
        """
        Итеративно ищет корень, спускаясь по касательной к функции.

        Args:
            target_delta (float): Целевое значение функции.
            initial_guess (float): Начальное приближение корня (стартовая точка). 
                По умолчанию 2.0.

        Returns:
            float: Приближенное значение корня.

        Raises:
            RuntimeError: Если производная близка к нулю (риск деления на ноль) 
                или если метод не сошелся за отведенное число итераций.
        """
        self.iterations = 0
        x = float(initial_guess)

        for _i in range(self.max_iter):
            self.iterations += 1
            fx = self.problem.f(x, target_delta)

            if abs(fx) < self.tol:
                return x

            dfx = self.problem.df(x)
            if abs(dfx) < 1e-12:
                raise RuntimeError("Производная близка к нулю. Деление на ноль.")

            x = x - fx / dfx

        raise RuntimeError(f"Метод Ньютона не сошелся за {self.max_iter} итераций")