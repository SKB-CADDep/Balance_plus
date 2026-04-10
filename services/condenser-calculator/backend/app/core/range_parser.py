import re
import logging

logger = logging.getLogger(__name__)

# Паттерн для поиска float чисел: поддерживает "5", "-5", "0.5", ".5", "-.5", "5."
FLOAT_PATTERN = r"-?\d*\.?\d+"

# Формат 4 (Start-End:Count), пример: 10-50:5 или -10-10:5
COUNT_REGEX = re.compile(rf"^({FLOAT_PATTERN})-({FLOAT_PATTERN}):(\d+)$")

# Формат 3 (Start-End-Step), пример: 10-50-10 или -5-5-2
STEP_REGEX = re.compile(rf"^({FLOAT_PATTERN})-({FLOAT_PATTERN})-({FLOAT_PATTERN})$")


def parse_range_input(raw: str) -> list[float]:
    """
    Парсит строку ввода в массив float.

    Форматы:
    1. "1000"           → [1000.0]
    2. "1000 2000 3000" → [1000.0, 2000.0, 3000.0]
    3. "10-50-10"       → [10.0, 20.0, 30.0, 40.0, 50.0]  (Start-End-Step)
    4. "10-50:5"        → [10.0, 20.0, 30.0, 40.0, 50.0]  (Start-End:Count)
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
