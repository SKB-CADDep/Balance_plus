import logging

import numpy as np
import pytest

from app.utils.table_models import Table1D, Table2D, interpolate_trilinear


logging.disable(logging.CRITICAL)


class TestOptimizedTable1D:
    """ Тесты для оптимизированного класса Table1D. """

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Настройка данных, которые будут использоваться в большинстве тестов.
        """
        self.x_data = np.array([15.3, 26.8, 38.4, 49.9, 61.5, 73.0])
        self.y_data = np.array([0.157, 0.258, 0.469, 0.607, 0.763, 0.919])

        self.table = Table1D(self.x_data, self.y_data, max_extrap_degree=3)

        self.expected_best_degree = 1

        p1_coeffs = np.polyfit(self.x_data, self.y_data, self.expected_best_degree)
        self.best_model = np.poly1d(p1_coeffs)

        self.expected_interp_val = 0.316
        self.expected_extrap_val_positive = self.best_model(125.0)  # ~1.6219
        self.expected_extrap_val_negative = self.best_model(-10.0)  # ~-0.1265

    # --- Тесты на создание объекта и подбор модели ---

    def test_creation_and_model_fitting(self):
        """
        Проверяет, что объект успешно создан и внутренняя модель для
        экстраполяции была правильно подобрана (степень 1).
        """
        assert self.table is not None
        assert self.table._best_extrap_degree == self.expected_best_degree
        assert isinstance(self.table._extrap_model, np.poly1d)

    def test_creation_with_unsorted_data(self):
        """
        Проверяет, что класс корректно работает с изначально
        неотсортированными данными.
        """
        x_unsorted = np.array([38.4, 15.3, 73.0])
        y_corresponding = np.array([0.469, 0.157, 0.919])
        table_unsorted = Table1D(x_unsorted, y_corresponding)
        assert np.array_equal(table_unsorted.x_cords, np.array([15.3, 38.4, 73.0]))
        assert table_unsorted(30.0) == pytest.approx(0.3555, abs=1e-3)

    def test_creation_fails(self):
        with pytest.raises(ValueError, match="Координаты X должны быть строго возрастающими"):
            Table1D(np.array([1, 2, 2]), np.array([1, 2, 3]))
        with pytest.raises(ValueError, match="Размеры x_cords и y_cords должны совпадать"):
            Table1D(np.array([1, 2]), np.array([1, 2, 3]))
        with pytest.raises(ValueError, match="Массивы координат не могут быть пустыми"):
            Table1D(np.array([]), np.array([]))

    # --- Тесты на вызов __call__ ---

    def test_call_for_interpolation(self):
        result = self.table(30.0)
        assert result == pytest.approx(self.expected_interp_val, abs=1e-3)

    def test_call_at_knot_point(self):
        result = self.table(self.x_data[2])
        assert result == self.y_data[2]

    def test_call_for_extrapolation(self):
        # ИСПРАВЛЕНИЕ 3: Теперь сравниваем с ожидаемыми значениями из ЛИНЕЙНОЙ модели
        result_pos = self.table(125.0)
        assert result_pos == pytest.approx(self.expected_extrap_val_positive, abs=1e-3)
        result_neg = self.table(-10.0)
        assert result_neg == pytest.approx(self.expected_extrap_val_negative, abs=1e-3)

    def test_call_with_mixed_array(self):
        test_points = np.array([30.0, 125.0, -10.0, 73.0])
        expected_results = np.array([
            self.expected_interp_val,
            self.expected_extrap_val_positive,
            self.expected_extrap_val_negative,
            self.y_data[-1]
        ])
        results = self.table(test_points)
        assert results.shape == expected_results.shape
        assert np.allclose(results, expected_results, atol=1e-3)

    def test_max_degree_handling(self):
        x_small = np.array([1, 2, 3, 4])
        y_small = np.array([1, 4, 9, 16])
        table_small = Table1D(x_small, y_small, max_extrap_degree=5)
        assert table_small._best_extrap_degree == 2


class TestTable2DAndTrilinear:
    """ Тесты для Table2D и трилинейной интерполяции. """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.x_cords = np.array([25.0, 30.0, 33.0, 35.0])
        self.y_cords = np.array([20.0, 50.0, 100.0, 150.0, 200.0])
        z_a1_original = np.array([
            [6.549, 7.211, 8.88, 10.945, 13.409], [5.9, 6.499, 8.018, 9.927, 12.214],
            [5.036, 5.552, 6.872, 8.572, 10.622], [3.851, 4.257, 5.299, 6.712, 8.438]
        ])
        z_a2_original = np.array([
            [6.635, 7.384, 9.285, 11.678, 14.582], [5.979, 6.655, 8.384, 10.591, 13.28],
            [5.104, 5.687, 7.184, 9.144, 11.546], [3.906, 4.362, 5.539, 7.158, 9.169]
        ])
        self.z_a1 = z_a1_original[::-1, :]
        self.z_a2 = z_a2_original[::-1, :]
        self.table_a1 = Table2D(self.x_cords, self.y_cords, self.z_a1)
        self.table_a2 = Table2D(self.x_cords, self.y_cords, self.z_a2)
        self.a_val1, self.a_val2 = 9000.0, 8000.0
        self.target_x, self.target_y = 27.0, 112.0

    def test_table2d_interpolation(self):
        result = self.table_a1(self.target_x, self.target_y)
        assert float(result) == pytest.approx(6.295, abs=1e-3)

    def test_table2d_out_of_bounds(self):
        assert np.isnan(self.table_a1(20.0, 50.0))

    def test_trilinear_interpolation(self):
        result = interpolate_trilinear(self.table_a2, self.a_val2, self.table_a1, self.a_val1,
                                       self.target_x, self.target_y, target_a=8800.0)
        assert result == pytest.approx(6.360, abs=1e-3)

    def test_trilinear_extrapolation_a_is_clamped(self):
        z_at_8000 = self.table_a2(self.target_x, self.target_y)
        result = interpolate_trilinear(self.table_a2, self.a_val2, self.table_a1, self.a_val1,
                                       self.target_x, self.target_y, target_a=7500.0)
        assert result == z_at_8000
