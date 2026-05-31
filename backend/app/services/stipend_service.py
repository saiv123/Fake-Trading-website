# Credits the monthly $250 stipend to active users — skips anyone whose last_active_at is more than 32 days ago
# and inserts a STIPEND transaction for those who qualify. No catch-up for missed months.
import calendar
from datetime import datetime, timedelta, date
from decimal import Decimal

from .. import db
from ..models.user import User
from ..models.transaction import Transaction
from . import notification_service

STIPEND_AMOUNT = Decimal('250.00')
INACTIVITY_DAYS = 32


def pay_stipends():
    """Run on the last calendar day of the month. Credits active users only."""
    cutoff = datetime.utcnow() - timedelta(days=INACTIVITY_DAYS)
    now = datetime.utcnow()

    for user in User.query.all():
        if user.last_active_at is None or user.last_active_at < cutoff:
            continue  # inactive — stipend forfeited, not retroactively paid
        user.balance = Decimal(str(user.balance)) + STIPEND_AMOUNT
        db.session.add(Transaction(
            user_id=user.id, type='STIPEND', total_value=STIPEND_AMOUNT,
            executed_at=now, notes='Monthly stipend',
        ))
        notification_service.create_notification(
            user.id, 'Stipend credited', f'Your monthly ${STIPEND_AMOUNT} stipend was added.')
    db.session.commit()


def get_stipend_status(user):
    cutoff = datetime.utcnow() - timedelta(days=INACTIVITY_DAYS)
    active = user.last_active_at is not None and user.last_active_at >= cutoff
    return {
        'next_stipend_date': _last_day_of_current_or_next_month().isoformat(),
        'amount':            str(STIPEND_AMOUNT),
        'active':            active,
        'last_active_at':    user.last_active_at.isoformat() if user.last_active_at else None,
    }


def _last_day_of_current_or_next_month() -> date:
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    if today.day < last_day:
        return date(today.year, today.month, last_day)
    # Today is the last day already — point to next month's last day
    year = today.year + (1 if today.month == 12 else 0)
    month = 1 if today.month == 12 else today.month + 1
    return date(year, month, calendar.monthrange(year, month)[1])
