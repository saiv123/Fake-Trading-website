# APScheduler job definitions — wires up all timed tasks (market open/close, hourly order check, corporate actions,
# stipend, tax settlement, fractional share audit, holiday calendar refresh). All cron times are US Eastern.
import os
from datetime import datetime
from decimal import Decimal

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .. import db
from ..models.stock import Stock
from ..models.holdings_ledger import HoldingLot
from ..models.user import User
from ..utils import market_hours
from ..utils.fractional import truncate_shares
from ..services import (
    stock_service, order_service, corporate_action_service,
    stipend_service, tax_service, notification_service,
)

ET = market_hours.ET
FMP_BASE = 'https://financialmodelingprep.com/api/v3'


def init_scheduler(app):
    """Create and start the scheduler. Call once from the app factory."""
    scheduler = BackgroundScheduler(timezone=ET)

    def job(fn, trading_day_only=False):
        def wrapper():
            with app.app_context():
                if trading_day_only and not market_hours.is_trading_day():
                    return
                try:
                    fn()
                except Exception as exc:  # never let a job crash the scheduler thread
                    app.logger.exception('Scheduled job %s failed: %s', fn.__name__, exc)
        return wrapper

    # FMP corporate actions fetch — 9:00 AM ET daily
    scheduler.add_job(job(corporate_action_service.fetch_corporate_actions),
                      CronTrigger(hour=9, minute=0))

    # Corporate actions processor — 9:25 AM ET, trading days
    scheduler.add_job(job(corporate_action_service.process_due_actions, trading_day_only=True),
                      CronTrigger(hour=9, minute=25))

    # Market open — 9:30 AM ET, trading days
    scheduler.add_job(job(_market_open_job, trading_day_only=True),
                      CronTrigger(day_of_week='mon-fri', hour=9, minute=30))

    # Hourly order check — 9:30–3:30 PM ET, trading days
    scheduler.add_job(job(order_service.check_pending_orders, trading_day_only=True),
                      CronTrigger(day_of_week='mon-fri', hour='10-15', minute=30))

    # Market close — 4:00 PM ET, trading days
    scheduler.add_job(job(_market_close_job, trading_day_only=True),
                      CronTrigger(day_of_week='mon-fri', hour=16, minute=0))

    # Fractional share audit — every hour
    scheduler.add_job(job(_fractional_audit), CronTrigger(minute=0))

    # Monthly stipend — last day of month, 6:00 PM ET
    scheduler.add_job(job(stipend_service.pay_stipends),
                      CronTrigger(day='last', hour=18, minute=0))

    # Market holiday calendar refresh — 1st of each month
    scheduler.add_job(job(_refresh_holidays), CronTrigger(day=1, hour=0, minute=5))

    # Tax warning banner — April 1st, 12:00 AM ET
    scheduler.add_job(job(_activate_tax_banner), CronTrigger(month=4, day=1, hour=0, minute=0))

    # Annual tax settlement — April 15th, 10:00 AM ET
    scheduler.add_job(job(tax_service.settle_all_users), CronTrigger(month=4, day=15, hour=10, minute=0))

    # Load holidays immediately so is_trading_day works before the first monthly refresh
    with app.app_context():
        try:
            _refresh_holidays()
        except Exception:
            app.logger.warning('Initial holiday calendar load failed')

    scheduler.start()
    return scheduler


# ---- Composite jobs ----------------------------------------------------------

def _market_open_job():
    stock_service.refresh_prices(_all_tickers())
    order_service.process_queued_orders()


def _market_close_job():
    stock_service.refresh_prices(_all_tickers())
    order_service.expire_all_pending()


def _fractional_audit():
    """Truncate any holdings qty with more than 2dp (defensive — columns are DECIMAL(15,2))."""
    fixed = 0
    for lot in HoldingLot.query.all():
        qty = Decimal(str(lot.qty_remaining))
        truncated = truncate_shares(qty)
        if truncated != qty:
            lot.qty_remaining = truncated
            fixed += 1
    if fixed:
        db.session.commit()


def _activate_tax_banner():
    """April 1st: notify every user who has an outstanding liability for the prior year."""
    year = datetime.utcnow().year - 1
    for user in User.query.all():
        liability = tax_service.compute_liability(user, year)
        if Decimal(liability['total_tax']) > 0:
            notification_service.create_notification(
                user.id, 'Tax settlement approaching',
                f"Your estimated {year} tax bill is ${liability['total_tax']}. "
                f"Auto-deduction occurs April 15th — ensure your cash covers it "
                f"or positions will be auto-liquidated.")
    db.session.commit()


def _refresh_holidays():
    """Pull US market holidays from FMP and load them into market_hours."""
    resp = requests.get(f'{FMP_BASE}/is-the-market-open',
                        params={'apikey': os.environ.get('FMP_API_KEY', '')}, timeout=15)
    if resp.status_code != 200:
        return
    data = resp.json()
    holidays = set()
    for entry in data.get('stockMarketHolidays', []):
        for key, value in entry.items():
            if key == 'year':
                continue
            parsed = _parse_date(value)
            if parsed:
                holidays.add(parsed)
    if holidays:
        market_hours.set_holidays(holidays)


# ---- Helpers -----------------------------------------------------------------

def _all_tickers():
    return [t[0] for t in db.session.query(Stock.ticker).filter(Stock.is_active.is_(True)).all()]


def _parse_date(value):
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
