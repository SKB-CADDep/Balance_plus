import numpy as np


def split_into_parts(number, n_parts):
    """
    Делит диапазон от 0 до number на n_parts равных интервалов.
    Возвращает массив из n_parts + 1 точек, которые являются границами этих интервалов.
    """
    return np.linspace(0, number, n_parts + 1)
