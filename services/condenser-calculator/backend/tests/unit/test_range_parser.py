"""
Юнит-тесты для парсера числовых диапазонов (range_parser)
Проверка форматов: одиночные числа, списки, Step (10-50-10) и Count (10-50:5)
"""

import pytest
from app.core.range_parser import parse_range_input


class TestRangeParser:

    def test_single_and_list_format(self):
        """Проверка форматов 1 и 2: Одиночное число и список через пробел"""
        assert parse_range_input("1000") == [1000.0]
        assert parse_range_input("10.5 20.5 30") == [10.5, 20.5, 30.0]
        assert parse_range_input("  -5  0  5  ") == [-5.0, 0.0, 5.0]

    def test_step_format(self):
        """Проверка формата 3: Start-End-Step (через дефис)"""
        # Положительный шаг
        assert parse_range_input("10-50-10") == [10.0, 20.0, 30.0, 40.0, 50.0]
        # Отрицательный шаг
        assert parse_range_input("50-10--10") == [50.0, 40.0, 30.0, 20.0, 10.0]
        # Дробные значения
        assert parse_range_input("0-1-0.25") == [0.0, 0.25, 0.5, 0.75, 1.0]

    def test_count_format(self):
        """Проверка формата 4: Start-End:Count (через двоеточие)"""
        # Разделение на 5 точек
        assert parse_range_input("10-50:5") == [10.0, 20.0, 30.0, 40.0, 50.0]
        # Две точки (только границы)
        assert parse_range_input("0-100:2") == [0.0, 100.0]
        # Одна точка (только старт)
        assert parse_range_input("10-50:1") == [10.0]
        # Отрицательные границы
        assert parse_range_input("-10-10:3") == [-10.0, 0.0, 10.0]

    def test_empty_input_error(self):
        """Проверка обработки пустой строки"""
        with pytest.raises(ValueError, match="Входная строка не может быть пустой"):
            parse_range_input("   ")

    def test_invalid_step_errors(self):
        """Проверка ошибок логики в формате Step"""
        # Шаг 0
        with pytest.raises(ValueError, match=r"Шаг \(Step\) не может быть равен нулю"):
            parse_range_input("10-50-0")

        # Шаг в обратную сторону
        with pytest.raises(ValueError, match="Направление шага не позволяет достичь"):
            parse_range_input("10-50--5")

    def test_invalid_count_errors(self):
        """Проверка ошибок логики в формате Count"""
        with pytest.raises(
            ValueError, match=r"Количество элементов \(Count\) должно быть >= 1"
        ):
            parse_range_input("10-50:0")

    def test_malformed_string_error(self):
        """Проверка полностью некорректного ввода"""
        with pytest.raises(ValueError, match="Неверный формат ввода"):
            parse_range_input("abc-def:ghi")

        with pytest.raises(ValueError, match="Неверный формат ввода"):
            parse_range_input("10---50")

    def test_floating_point_precision(self):
        """Проверка точности округления (8 знаков)"""
        # 0.1 + 0.2 в Python обычно не равно 0.3, но наш парсер должен округлять
        result = parse_range_input("0.1-0.3:3")
        assert result == [0.1, 0.2, 0.3]
