# Helpers for determining if the market is currently open, whether today is a trading day, and tracking the FMP holiday calendar
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo('America/New_York')

MARKET_OPEN  = time(9, 30)
MARKET_CLOSE = time(16, 0)

# Populated by the monthly Market Holiday Calendar Refresh job (set of date objects)
_holidays: set = set()


def set_holidays(holiday_dates):
    """Replace the in-memory holiday set. Called by the calendar refresh job."""
    global _holidays
    _holidays = set(holiday_dates)


def now_et() -> datetime:
    return datetime.now(ET)


def is_trading_day(d: date = None) -> bool:
    d = d or now_et().date()
    if d.weekday() >= 5:          # Saturday/Sunday
        return False
    return d not in _holidays


def is_market_open(dt: datetime = None) -> bool:
    dt = dt or now_et()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ET)
    if not is_trading_day(dt.date()):
        return False
    return MARKET_OPEN <= dt.time() < MARKET_CLOSE


def market_close_dt(d: date = None) -> datetime:
    """The 4:00 PM ET close datetime for the given trading day."""
    d = d or now_et().date()
    return datetime.combine(d, MARKET_CLOSE, tzinfo=ET)


def next_market_open_dt(dt: datetime = None) -> datetime:
    """The next 9:30 AM ET open at or after dt, skipping weekends and holidays."""
    dt = dt or now_et()
    candidate = datetime.combine(dt.date(), MARKET_OPEN, tzinfo=ET)
    if dt.time() >= MARKET_OPEN or not is_trading_day(dt.date()):
        candidate += timedelta(days=1)
    while not is_trading_day(candidate.date()):
        candidate += timedelta(days=1)
    return candidate
