"""User profile endpoints (/api/user).

Profile read/update plus the user's notifications and stipend status. Updates are restricted: only
display_name and the drip_all UI flag are editable — any attempt to change money/identity fields
(balance, starting_balance, email, OAuth/Discord IDs) is rejected with 403.
"""
from flask import Blueprint, request, jsonify, g
from ..utils.auth import require_session_or_bot_user
from ..services.stipend_service import get_stipend_status
from ..services.notification_service import get_notifications
from .. import db

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# Fields a PUT /me may never change — guarded with a 403
_IMMUTABLE_FIELDS = {'starting_balance', 'balance', 'email', 'google_id', 'microsoft_id', 'discord_id'}


@user_bp.route('/me')
@require_session_or_bot_user
def get_me():
    """GET /api/user/me — the acting user's profile, balance, state, and Discord-link status."""
    u = g.user
    return jsonify({
        'id':              u.id,
        'email':           u.email,
        'display_name':    u.display_name,
        'balance':         str(u.balance),
        'starting_balance': str(u.starting_balance),
        'state':           u.state,
        'discord_linked':  u.discord_id is not None,
        'drip_all':        u.drip_all,
        'created_at':      u.created_at.isoformat(),
    })


@user_bp.route('/me', methods=['PUT'])
@require_session_or_bot_user
def update_me():
    """PUT /api/user/me — update display_name / drip_all only; 403 on any protected field."""
    data = request.get_json()

    if any(k in data for k in _IMMUTABLE_FIELDS):
        return jsonify({'error': 'Cannot modify protected fields'}), 403

    if 'display_name' in data:
        g.user.display_name = data['display_name']

    if 'drip_all' in data:
        g.user.drip_all = bool(data['drip_all'])

    db.session.commit()
    return jsonify({'message': 'Profile updated'})


@user_bp.route('/notifications')
@require_session_or_bot_user
def notifications():
    """GET /api/user/notifications — recent alerts (corporate actions, stipends, tax)."""
    return jsonify(get_notifications(g.user))


@user_bp.route('/stipend/status')
@require_session_or_bot_user
def stipend_status():
    """GET /api/user/stipend/status — next stipend date and whether the user counts as active."""
    return jsonify(get_stipend_status(g.user))
