from flask import Blueprint, request, jsonify, g
from ..utils.auth import require_api_key
from ..services.stipend_service import get_stipend_status
from ..services.notification_service import get_notifications
from .. import db

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

_IMMUTABLE_FIELDS = {'starting_balance', 'balance', 'email', 'google_id', 'microsoft_id', 'discord_id'}


@user_bp.route('/me')
@require_api_key
def get_me():
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
@require_api_key
def update_me():
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
@require_api_key
def notifications():
    return jsonify(get_notifications(g.user))


@user_bp.route('/stipend/status')
@require_api_key
def stipend_status():
    return jsonify(get_stipend_status(g.user))
