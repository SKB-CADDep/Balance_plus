"""
Инструмент для парсинга строковых диапазонов в массивы чисел.

Предоставляет утилиты для преобразования удобного пользовательского ввода 
(например, "10-50-10" или "10-50:5") в строгие списки чисел с плавающей 
точкой (float), которые требуются расчетному ядру для генерации матриц режимов.
Улучшает UX фронтенда, избавляя пользователя от необходимости вручную вводить 
длинные массивы данных.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Регулярное выражение для поиска чисел с плавающей точкой.
# Поддерживает отрицательные значения ("-5"), опущенные нули (".5", "5.") и стандартные целые ("5").
FLOAT_PATTERN = r"-?\d*\.?\d+"

# Компиляция regex для формата "Start-End:Count".
# Пример: 10-50:5 (от 10 до 50, разбить на 5 точек) или -10-10:5 (от -10 до 10 на 5 точек).
COUNT_REGEX = re.compile(rf"^({FLOAT_PATTERN})-({FLOAT_PATTERN}):(\d+)$")

# Компиляция regex для формата "Start-End-Step".
# Пример: 10-50-10 (от 10 до 50 с шагом 10) или -5-5-2 (от -5 до 5 с шагом 2).
STEP_REGEX = re.compile(rf"^({FLOAT_PATTERN})-({FLOAT_PATTERN})-({FLOAT_PATTERN})$")


def parse_range_input(raw: str) -> list[float]:
    """
    Разбирает (парсит) входную строку в массив вещественных чисел.

    Поддерживает 4 различных формата пользовательского ввода. 
    При разворачивании диапазонов использует округление (round) до 8-го знака 
    для предотвращения классической проблемы накопления ошибки в математике 
    с плавающей точкой (например, 0.1 + 0.2 = 0.30000000000000004).

    Поддерживаемые форматы:
    1. Одиночное число:  "1000"           → [1000.0]
    2. Список чисел:     "1000 2000 3000" → [1000.0, 2000.0, 3000.0]
    3. Start-End-Step:   "10-50-10"       → [10.0, 20.0, 30.0, 40.0, 50.0]
    4. Start-End:Count:  "10-50:5"        → [10.0, 20.0, 30.0, 40.0, 50.0]

    Args:
        raw (str): Исходная "сырая" строка от пользователя.

    Returns:
        list[float]: Сгенерированный список числовых значений.

    Raises:
        ValueError: Если строка пуста, имеет неверный формат, задан нулевой шаг 
            или направление шага конфликтует с границами (например, от 10 до 50 с шагом -5).
    """
    raw = raw.strip()
    if not raw:
        logger.warning("Попытка парсинга пустой строки")
        raise ValueError("Входная строка не может быть пустой.")

    # Формат 4 (Start-End:Count)
    match_count = COUNT_REGEX.match(raw)
    if match_count:
        start, end = float(match_count.group(1)), float(match_count.group(2))
        count = int(match_count.group(3))

        if count <= 0:
            logger.error(
                f"Некорректное количество элементов (Count) '{count}' во вводе: '{raw}'"
            )
            raise ValueError("Количество элементов (Count) должно быть >= 1.")
        if count == 1:
            return [start]

        step = (end - start) / (count - 1)
        result = [round(start + i * step, 8) for i in range(count)]
        logger.debug(f"Успешно распаршен формат Count: '{raw}' -> {result}")
        return result

    # Формат 3 (Start-End-Step)
    match_step = STEP_REGEX.match(raw)
    if match_step:
        start, end, step = map(float, match_step.groups())

        if step == 0:
            logger.error(f"Нулевой шаг в строке: '{raw}'")
            raise ValueError("Шаг (Step) не может быть равен нулю.")

        # Защита от бесконечных циклов: проверка направления шага
        if (end > start and step < 0) or (end < start and step > 0):
            logger.error(f"Конфликт направления шага и границ в строке: '{raw}'")
            raise ValueError(
                "Направление шага не позволяет достичь конечного значения."
            )

        num_elements = int((end - start) / step) + 1
        result = [round(start + i * step, 8) for i in range(num_elements)]

        logger.debug(f"Успешно распаршен формат Step: '{raw}' -> {result}")
        return result

    # Форматы 1 и 2 (числа, разделённые пробелами)
    try:
        result = [float(x) for x in raw.split()]
        if not result:
            raise ValueError("Не найдено чисел для парсинга.")

        logger.debug(f"Успешно распаршен формат List/Single: '{raw}' -> {result}")
        return result

    except ValueError:
        logger.error(f"Не удалось распознать формат строки: '{raw}'")
        raise ValueError(f"Неверный формат ввода: '{raw}'")