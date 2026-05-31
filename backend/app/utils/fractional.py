# Truncation (floor) to 2 decimal places for fractional share quantities — used by DRIP, reverse splits, and dollar-amount buys; never rounds up
from decimal import Decimal, ROUND_DOWN

TWO_PLACES = Decimal('0.01')
FOUR_PLACES = Decimal('0.0001')


def truncate_shares(value) -> Decimal:
    """Floor a share quantity to 2 decimal places. Remainders are discarded (disclosed in ToS)."""
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_DOWN)


def truncate_money(value) -> Decimal:
    """Floor a cash amount to 2 decimal places."""
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_DOWN)


def to_price(value) -> Decimal:
    """Normalise a price to 4 decimal places (matches the DECIMAL(15,4) columns)."""
    return Decimal(str(value)).quantize(FOUR_PLACES, rounding=ROUND_DOWN)
