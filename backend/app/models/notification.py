# Per-user notifications — created when a corporate action, stipend, or tax event affects the user; surfaced in the UI and DM'd via Discord if linked
from datetime import datetime
from .. import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    message    = db.Column(db.String(1000), nullable=False)
    ticker     = db.Column(db.String(10))
    read       = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('idx_notif_user', 'user_id', 'created_at'),
    )

    def to_dict(self):
        return {
            'id':         self.id,
            'title':      self.title,
            'message':    self.message,
            'ticker':     self.ticker,
            'read':       self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
