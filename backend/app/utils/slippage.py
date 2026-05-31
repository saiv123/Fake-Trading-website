# Implements the grace window and half-difference slippage model for limit and stop orders checked hourly rather than per-second.
# Returns the fill price (Decimal) if the order should execute at the given market price, or None if it should not.
from decimal import Decimal

GRACE = Decimal('1.00')   # within $1 of the target, fill at market (grace window)


def evaluate_fill(direction: str, order_type: str, market_price,
                  limit_price=None, stop_price=None):
    """direction: BUY|SELL, order_type: MARKET|LIMIT|STOP|STOP_LIMIT.
    Returns a Decimal fill price or None if the order does not trigger."""
    p = Decimal(str(market_price))

    if order_type == 'MARKET':
        return p

    if order_type == 'LIMIT':
        return _limit_fill(direction, p, Decimal(str(limit_price)))

    if order_type == 'STOP':
        # Stop becomes a market order once triggered
        return _stop_fill(direction, p, Decimal(str(stop_price)))

    if order_type == 'STOP_LIMIT':
        # Trigger at stop, then only fill if it satisfies the limit
        if not _stop_triggered(direction, p, Decimal(str(stop_price))):
            return None
        return _limit_fill(direction, p, Decimal(str(limit_price)))

    return None


def _limit_fill(direction: str, p: Decimal, limit: Decimal):
    if direction == 'BUY':
        # Execute when price <= limit
        if p <= limit:
            return p
        diff = p - limit
        if diff <= GRACE:
            return p
        return limit + (diff / 2)
    else:  # SELL — execute when price >= limit
        if p >= limit:
            return p
        diff = limit - p
        if diff <= GRACE:
            return p
        return limit - (diff / 2)


def _stop_triggered(direction: str, p: Decimal, stop: Decimal) -> bool:
    # SELL stop (stop-loss): triggers when price <= stop
    # BUY stop: triggers when price >= stop
    return p <= stop if direction == 'SELL' else p >= stop


def _stop_fill(direction: str, p: Decimal, stop: Decimal):
    if direction == 'SELL':
        if p >= stop:
            return None
        diff = stop - p
        if diff <= GRACE:
            return p
        return stop - (diff / 2)
    else:  # BUY stop
        if p <= stop:
            return None
        diff = p - stop
        if diff <= GRACE:
            return p
        return stop + (diff / 2)
