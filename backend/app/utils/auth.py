# Route auth decorators — all callers must present a known API key in X-API-Key
import os
from datetime import datetime
from functools import wraps
from flask import request, jsonify, g
from ..models.user import User
from .. import db

# Discard empty values so a missing env var can't be matched by an empty/absent header
_VALID_API_KEYS = {k for k in (os.environ.get('WEBSITE_API_KEY'),
                               os.environ.get('BOT_API_KEY')) if k}


def _resolve_user():
    """The bot sends X-Discord-Id; the website sends X-User-Id. Either identifies the acting user."""
    user_id = request.headers.get('X-User-Id')
    if user_id:
        return User.query.get(user_id)
    discord_id = request.headers.get('X-Discord-Id')
    if discord_id:
        return User.query.filter_by(discord_id=discord_id).first()
    return None


def require_api_key(f):
    """Rejects requests that don't carry a recognised X-API-Key, then resolves and injects the acting user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') not in _VALID_API_KEYS:
            return jsonify({'error': 'Unauthorized'}), 401

        user = _resolve_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.last_active_at = datetime.utcnow()
        db.session.commit()

        g.user = user
        return f(*args, **kwargs)
    return decorated


def require_any_key(f):
    """For routes that need auth but no specific user — e.g. the Discord link token endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') not in _VALID_API_KEYS:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated
