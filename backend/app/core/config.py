"""Shared numeric constants used by the backend simulation engine.

Keeping these values in one place makes the mathematical model easier to audit.
If the project later needs another lottery or another ticket price, most low-level
helpers can stay unchanged and only these configuration values need to be updated.
"""

# Official Eurojackpot ticket price used in the simulation.
TICKET_PRICE_EUR = 2.0

# Main draw configuration: choose 5 unique numbers from 1 to 50.
MAIN_NUMBERS_COUNT = 5
MAIN_NUMBERS_MIN = 1
MAIN_NUMBERS_MAX = 50

# Euro number configuration: choose 2 unique numbers from 1 to 12.
EURO_NUMBERS_COUNT = 2
EURO_NUMBERS_MIN = 1
EURO_NUMBERS_MAX = 12
