from __future__ import annotations

from dataclasses import dataclass

LOTTO45_BASE_SELECTION_RATE = 6 / 45

# Точные опорные значения, которые явно указаны в статье / на скрине.
LOTTO45_ANCHOR_SELECTION_RATES: dict[int, float] = {
    7: 0.163,
    11: 0.165,
    37: 0.103,
    38: 0.105,
}

POPULAR_MAIN_NUMBERS = {7, 11, 13, 21, 23, 42}


@dataclass(frozen=True)
class NumberWeight:
    number: int
    relative_weight: float


def _anchor_relative_weight(selection_rate: float) -> float:
    return selection_rate / LOTTO45_BASE_SELECTION_RATE


def _smooth_base_relative_weight(number: int) -> float:
    """
    Приближённый гладкий тренд:
    маленькие числа немного популярнее, большие немного менее популярны.
    Для 1..45 задаём линейный спад от 1.15 к 0.85.
    """
    if not 1 <= number <= 45:
        raise ValueError("This smooth profile is defined only for numbers 1..45.")

    start = 1.15
    end = 0.85
    slope = (end - start) / (45 - 1)
    return start + slope * (number - 1)


def _tail_extension_relative_weight(number: int) -> float:
    """
    Для 46..50 делаем продолжение хвоста:
    новые числа считаем слегка менее популярными, чем 41..45.
    """
    if not 46 <= number <= 50:
        raise ValueError("Tail extension is defined only for numbers 46..50.")

    # Плавное продолжение после 45-го числа.
    # 45 ≈ 0.85, дальше ещё небольшой спад.
    return 0.85 - 0.01 * (number - 45)


def get_main_number_relative_weights() -> dict[int, float]:
    """
    Возвращает относительные веса 1..50.
    Это НЕ вероятности, а relative popularity weights.

    Метод:
    1) гладкий тренд для 1..45
    2) точные anchor overrides для 7, 11, 37, 38
    3) экстраполяция хвоста для 46..50
    """
    weights: dict[int, float] = {}

    for number in range(1, 46):
        weights[number] = _smooth_base_relative_weight(number)

    for number, rate in LOTTO45_ANCHOR_SELECTION_RATES.items():
        weights[number] = _anchor_relative_weight(rate)

    for number in range(46, 51):
        weights[number] = _tail_extension_relative_weight(number)

    return weights


def get_main_number_probabilities() -> dict[int, float]:
    """
    Нормализованные вероятности для weighted sampling.
    """
    relative_weights = get_main_number_relative_weights()
    total = sum(relative_weights.values())

    if total <= 0:
        raise ValueError("Sum of relative weights must be positive.")

    return {number: weight / total for number, weight in relative_weights.items()}


def get_anti_popular_main_number_probabilities() -> dict[int, float]:
    """
    Инвертированная версия popularity model:
    чем популярнее число, тем ниже его вероятность выбора.
    """
    relative_weights = get_main_number_relative_weights()
    inverted = {number: 1.0 / weight for number, weight in relative_weights.items()}
    total = sum(inverted.values())

    if total <= 0:
        raise ValueError("Sum of inverted weights must be positive.")

    return {number: weight / total for number, weight in inverted.items()}


def get_birthday_main_number_probabilities() -> dict[int, float]:
    """
    Упрощённая birthday strategy:
    используем только числа 1..31, равномерно.
    """
    probabilities: dict[int, float] = {}

    for number in range(1, 51):
        probabilities[number] = 1 / 31 if 1 <= number <= 31 else 0.0

    return probabilities


def get_uniform_main_number_probabilities() -> dict[int, float]:
    return {number: 1 / 50 for number in range(1, 51)}


def compute_ticket_popularity_score(main_numbers: set[int] | frozenset[int]) -> float:
    """
    Индекс популярности билета.
    Он не является вероятностью; это feature для будущей share model.

    Базовая идея:
    - средний относительный вес чисел из статьи / адаптации
    - бонус за числа 1..31
    - бонус за популярные числа
    - бонус за последовательности
    """
    if len(main_numbers) != 5:
        raise ValueError("Main numbers must contain exactly 5 unique numbers.")

    relative_weights = get_main_number_relative_weights()

    avg_weight = sum(relative_weights[number] for number in main_numbers) / 5

    score = avg_weight

    low_numbers_count = sum(1 for number in main_numbers if number <= 31)
    score += 0.05 * low_numbers_count

    popular_count = sum(1 for number in main_numbers if number in POPULAR_MAIN_NUMBERS)
    score += 0.07 * popular_count

    sorted_numbers = sorted(main_numbers)
    consecutive_pairs = sum(
        1
        for left, right in zip(sorted_numbers, sorted_numbers[1:])
        if right - left == 1
    )
    score += 0.08 * consecutive_pairs

    return score