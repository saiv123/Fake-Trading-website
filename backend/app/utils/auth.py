# Route auth decorators.
#
# Two distinct trust mechanisms, not one shared "API key" concept:
#   - Session tokens authenticate a specific logged-in website user. Minted at OAuth login
#     (see create_session_token), sent back as `Authorization: Bearer <token>`, and verified
#     here by signature — nothing about them is guessable or shared between users.
#   - BOT_API_KEY authenticates exactly one thing: our own Discord bot process. It never leaves
#     bot-controlled hardware, so it's a real secret — unlike a key that ships inside a public
#     frontend bundle. It still needs X-Discord-Id to say which linked account the bot is acting
#     for; the key alone only proves "this is our bot", not "this is user X".
import os
from datetime import datetime
from functools import wraps
from flask import request, jsonify, g, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from ..models.user import User
from .. import db

BOT_API_KEY = os.environ.get('BOT_API_KEY')

SESSION_SALT = 'user-session-v1'
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt=SESSION_SALT)


def create_session_token(user_id: int) -> str:
    """Mint a signed, expiring session token for one specific user. Called once, at successful
    OAuth login/registration — this is the only credential that authenticates the website."""
    return _serializer().dumps({'user_id': user_id})


def _user_from_session_token(token: str):
    try:
        data = _serializer().loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return User.query.get(data.get('user_id'))


def _touch(user):
    user.last_active_at = datetime.utcnow()
    db.session.commit()


def require_session(f):
    """Website-only routes: caller must present a valid Authorization: Bearer <session token>."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else None
        user = _user_from_session_token(token) if token else None
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        _touch(user)
        g.user = user
        return f(*args, **kwargs)
    return decorated


def require_bot(f):
    """Bot-only routes with no per-user identity yet (e.g. minting a Discord link token before any
    account is linked) — BOT_API_KEY just proves the caller is our bot process."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not BOT_API_KEY or request.headers.get('X-API-Key') != BOT_API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def require_bot_user(f):
    """Bot routes acting on behalf of a linked user: BOT_API_KEY identifies the bot, X-Discord-Id
    says which account it's acting for."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not BOT_API_KEY or request.headers.get('X-API-Key') != BOT_API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        discord_id = request.headers.get('X-Discord-Id')
        user = User.query.filter_by(discord_id=discord_id).first() if discord_id else None
        if not user:
            return jsonify({'error': 'User not found'}), 404
        _touch(user)
        g.user = user
        return f(*args, **kwargs)
    return decorated


def require_session_or_bot_user(f):
    """Routes both the website and the Discord bot call: website via session token, bot via
    BOT_API_KEY + X-Discord-Id. Exactly one of the two must succeed."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else None
        if token:
            user = _user_from_session_token(token)
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            _touch(user)
            g.user = user
            return f(*args, **kwargs)

        if BOT_API_KEY and request.headers.get('X-API-Key') == BOT_API_KEY:
            discord_id = request.headers.get('X-Discord-Id')
            user = User.query.filter_by(discord_id=discord_id).first() if discord_id else None
            if not user:
                return jsonify({'error': 'User not found'}), 404
            _touch(user)
            g.user = user
            return f(*args, **kwargs)

        return jsonify({'error': 'Unauthorized'}), 401
    return decorated
