from datetime import datetime, date

from app.utils import market_hours
from app.utils.market_hours import ET, is_market_open, is_trading_day, set_holidays


def test_open_during_trading_hours_on_a_weekday():
    # Wednesday 2024-06-12, 11:00 AM ET
    set_holidays(set())
    dt = datetime(2024, 6, 12, 11, 0, tzinfo=ET)
    assert is_market_open(dt) is True


def test_closed_before_open():
    set_holidays(set())
    dt = datetime(2024, 6, 12, 9, 0, tzinfo=ET)
    assert is_market_open(dt) is False


def test_closed_after_close():
    set_holidays(set())
    dt = datetime(2024, 6, 12, 16, 30, tzinfo=ET)
    assert is_market_open(dt) is False


def test_closed_on_weekend():
    set_holidays(set())
    saturday = datetime(2024, 6, 15, 11, 0, tzinfo=ET)
    assert is_market_open(saturday) is False


def test_holiday_is_not_a_trading_day():
    holiday = date(2024, 7, 4)
    set_holidays({holiday})
    assert is_trading_day(holiday) is False
    set_holidays(set())  # reset for other tests


def test_close_boundary_is_exclusive():
    set_holidays(set())
    dt = datetime(2024, 6, 12, 16, 0, tzinfo=ET)  # exactly 4:00 PM
    assert is_market_open(dt) is False
