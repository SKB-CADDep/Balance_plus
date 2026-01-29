import math


class ProblemDefinition:
    """
    Инкапсулирует математическую постановку задачи: расчет A3_delt и его производной.
    Это позволяет менять формулы в одном месте, не затрагивая алгоритмы решения.
    """

    def __init__(self):
        """Вычисляет и кэширует константы один раз для производительности."""
        pi = 3.1415
        e_approx = 2.71
        power = 0.83

        # A3_delt = 1 - C * X^(power-1)
        self.c = (pi / e_approx) ** power
        self.power_minus_1 = power - 1.0  # -0.17

    def calculate_delta(self, x: float) -> float:
        """Рассчитывает A3_delt для заданного X."""
        if x <= 0:
            return float('nan')  # Возведение отрицательного числа в дробную степень не определено в R
        return 1.0 - self.c * math.pow(x, self.power_minus_1)

    def f(self, x: float, target_delta: float) -> float:
        """Целевая функция, корень которой мы ищем: F(X) = A3_delt(X) - target_delta."""
        return self.calculate_delta(x) - target_delta

    def df(self, x: float) -> float:
        """Производная функции F(X) по X. Нужна для метода Ньютона."""
        # d/dx (1 - C*x^p - T) = -C * p * x^(p-1)
        # где p = self._power_minus_1
        if x <= 0:
            return float('nan')
        return -self.c * self.power_minus_1 * math.pow(x, self.power_minus_1 - 1.0)
