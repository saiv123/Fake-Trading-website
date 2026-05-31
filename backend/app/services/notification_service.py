# Creates and reads per-user notifications — written when a corporate action, stipend, or tax event affects the user; surfaced in the UI and DM'd via Discord if linked
from .. import db
from ..models.notification import Notification


def create_notification(user_id: int, title: str, message: str, ticker: str = None) -> Notification:
    """Insert a notification. Caller is responsible for committing (so it can be part of a larger transaction)."""
    notif = Notification(user_id=user_id, title=title, message=message, ticker=ticker)
    db.session.add(notif)
    return notif


def get_notifications(user, limit: int = 50):
    rows = (Notification.query
            .filter_by(user_id=user.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all())
    return [n.to_dict() for n in rows]


def mark_all_read(user):
    Notification.query.filter_by(user_id=user.id, read=False).update({'read': True})
    db.session.commit()
