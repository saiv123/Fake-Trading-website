from decimal import Decimal

from app.utils.slippage import evaluate_fill


def D(x):
    return Decimal(str(x))


# ---- BUY limit ---------------------------------------------------------------

def test_buy_limit_below_limit_fills_at_market():
    # price under the limit → ideal fill at market price
    assert evaluate_fill('BUY', 'LIMIT', 95, limit_price=100) == D(95)


def test_buy_limit_within_grace_window_fills_at_market():
    # price $0.50 over the limit → within $1 grace → fill at market
    assert evaluate_fill('BUY', 'LIMIT', 100.50, limit_price=100) == D('100.50')


def test_buy_limit_beyond_grace_applies_half_difference():
    # price $3 over the limit → fill at limit + half the excess = 100 + 1.5
    assert evaluate_fill('BUY', 'LIMIT', 103, limit_price=100) == D('101.5')


# ---- SELL limit --------------------------------------------------------------

def test_sell_limit_above_limit_fills_at_market():
    assert evaluate_fill('SELL', 'LIMIT', 105, limit_price=100) == D(105)


def test_sell_limit_beyond_grace_applies_half_difference():
    # price $4 under the limit → fill at limit - half = 100 - 2
    assert evaluate_fill('SELL', 'LIMIT', 96, limit_price=100) == D('98')


# ---- SELL stop (stop-loss) ---------------------------------------------------

def test_sell_stop_not_triggered_above_stop():
    assert evaluate_fill('SELL', 'STOP', 105, stop_price=100) is None


def test_sell_stop_within_grace_fills_at_market():
    assert evaluate_fill('SELL', 'STOP', 99.50, stop_price=100) == D('99.50')


def test_sell_stop_beyond_grace_applies_half_difference():
    # $5 below stop → stop - half = 100 - 2.5
    assert evaluate_fill('SELL', 'STOP', 95, stop_price=100) == D('97.5')


# ---- BUY stop ----------------------------------------------------------------

def test_buy_stop_not_triggered_below_stop():
    assert evaluate_fill('BUY', 'STOP', 95, stop_price=100) is None


def test_buy_stop_beyond_grace_applies_half_difference():
    assert evaluate_fill('BUY', 'STOP', 105, stop_price=100) == D('102.5')


# ---- STOP_LIMIT --------------------------------------------------------------

def test_stop_limit_not_triggered_returns_none():
    # SELL stop-limit not triggered while price above stop
    assert evaluate_fill('SELL', 'STOP_LIMIT', 105, stop_price=100, limit_price=98) is None


def test_stop_limit_triggered_then_honors_limit():
    # Triggered (price <= stop), then evaluated as a sell limit at the given price
    assert evaluate_fill('SELL', 'STOP_LIMIT', 99, stop_price=100, limit_price=98) == D(99)


# ---- MARKET ------------------------------------------------------------------

def test_market_always_fills_at_price():
    assert evaluate_fill('BUY', 'MARKET', 42.42) == D('42.42')
