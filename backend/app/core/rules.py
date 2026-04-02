"""Mapping between match combinations and Eurojackpot prize classes.

The evaluator counts how many main numbers and euro numbers a ticket matched.
This file converts that pair into the corresponding named prize class.
"""

# Keys are tuples in the form: (matched_main_numbers, matched_euro_numbers).
PRIZE_CLASSES: dict[tuple[int, int], str] = {
    (5, 2): "Class 1",
    (5, 1): "Class 2",
    (5, 0): "Class 3",
    (4, 2): "Class 4",
    (4, 1): "Class 5",
    (3, 2): "Class 6",
    (4, 0): "Class 7",
    (2, 2): "Class 8",
    (3, 1): "Class 9",
    (3, 0): "Class 10",
    (1, 2): "Class 11",
    (2, 1): "Class 12",
}
