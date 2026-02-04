import numpy as np
import pytest

from app.utils.division_range import split_into_parts


class TestSplitIntoParts:
    """
    Набор тестов для функции split_into_parts.
    """

    def test_basic_functionality(self):
        """
        Тестирует базовый случай: деление числа на несколько частей.
        """
        number = 1000
        n_parts = 10
        expected = np.array([0., 100., 200., 300., 400., 500., 600., 700., 800., 900., 1000.])
        result = split_into_parts(number, n_parts)
        assert np.array_equal(result, expected)  # проверка идентичности

    def test_output_properties(self):
        """
        Проверяет ключевые свойства выходного массива: длину, начальную и конечную точки.
        """
        number = 50
        n_parts = 5
        result = split_into_parts(number, n_parts)

        assert len(result) == n_parts + 1  # длина

        assert result[0] == 0  # начальная точка

        assert result[-1] == number  # конечная точка

    def test_edge_case_one_part(self):
        """
        Тестирует граничный случай, когда число делится всего на одну часть.
        """
        number = 123
        n_parts = 1
        expected = np.array([0., 123.])
        result = split_into_parts(number, n_parts)
        assert np.array_equal(result, expected)

    def test_edge_case_zero_number(self):
        """
        Тестирует граничный случай, когда делится ноль.
        """
        number = 0
        n_parts = 10
        expected = np.zeros(n_parts + 1)  # Массив из одиннадцати нулей
        result = split_into_parts(number, n_parts)
        assert np.array_equal(result, expected)
        assert len(result) == 11

    def test_float_number_input(self):
        """
        Проверяет корректность работы с числом с плавающей точкой.
        """
        number = 10.5
        n_parts = 3
        expected = np.array([0., 3.5, 7.0, 10.5])
        result = split_into_parts(number, n_parts)
        assert np.allclose(result, expected)

    def test_invalid_input_negative_parts(self):
        """
        Проверяет, что функция вызывает ошибку при отрицательном количестве частей.
        `np.linspace` должен вызвать ValueError, если `num` < 0.
        """
        with pytest.raises(ValueError):
            split_into_parts(100, -5)

    def test_invalid_input_zero_parts(self):
        """
        Проверяет поведение при n_parts=0. np.linspace(start, stop, 1) вернет массив [stop].
        Наша функция вернет [number]. Это не ошибка, но поведение стоит задокументировать тестом.
        """
        number = 100
        n_parts = 0
        expected = np.array([0.])
        result = split_into_parts(number, n_parts)
        assert np.array_equal(result, expected)
