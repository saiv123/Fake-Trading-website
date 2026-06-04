"""Notification service.

Creates and reads per-user notifications written when an event touches an account (corporate actions,
stipends, taxes). create_notification deliberately does not commit, so it can join the same DB
transaction as the event that triggered it.
"""
from .. import db
from ..models.notification import Notification


def create_notification(user_id: int, title: str, message: str, ticker: str = None) -> Notification:
    """Insert a notification. Caller is responsible for committing (so it can be part of a larger transaction)."""
    notif = Notification(user_id=user_id, title=title, message=message, ticker=ticker)
    db.session.add(notif)
    return notif


def get_notifications(user, limit: int = 50):
    """Return the user's most recent notifications (newest first)."""
    rows = (Notification.query
            .filter_by(user_id=user.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all())
    return [n.to_dict() for n in rows]


def mark_all_read(user):
    """Mark all of the user's unread notifications as read."""
    Notification.query.filter_by(user_id=user.id, read=False).update({'read': True})
    db.session.commit()
