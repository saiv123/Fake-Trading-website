"""Authentication & account-linking endpoints (/api/auth).

Login is OAuth-only (Google / Microsoft) — there are no passwords. The flow:
  1. /<provider> redirects to the provider; /<provider>/callback handles the return.
  2. _handle_oauth matches the account by provider ID, links it to an existing email if found,
     or redirects to FRONTEND_URL/auth/callback with requires_registration params so the SPA can
     collect starting_balance + state.
  3. /oauth/register finalizes a brand-new account.
Every callback ends in a redirect to the frontend (never raw JSON) since the browser is on the
Flask origin at that point and needs to land back in the SPA — see _handle_oauth.
Also hosts the Discord linking flow: the bot requests a one-time token, the user visits the URL on
the website, and discord_id gets written onto their account. Link tokens are short-lived and in-memory.
"""
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask import Blueprint, request, jsonify, redirect, url_for, current_app, g
from authlib.integrations.flask_client import OAuth

from ..models.user import User
from ..utils.auth import require_bot, require_session, create_session_token
from .. import db

# Short-lived Discord link tokens — { token: { discord_id, expires_at } }
# Kept in memory since they expire in 15 minutes and don't need to survive restarts
_discord_link_tokens: dict = {}

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

oauth = OAuth()

BALANCE_MIN =     1_000.00
BALANCE_MAX = 100_000.00


def init_oauth(app):
    """Call from the app factory to register OAuth providers."""
    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

    oauth.register(
        name='microsoft',
        client_id=app.config['MICROSOFT_CLIENT_ID'],
        client_secret=app.config['MICROSOFT_CLIENT_SECRET'],
        server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


# ---- Google OAuth ------------------------------------------------------------

@auth_bp.route('/google')
def google_login():
    """GET /api/auth/google — kick off the Google OAuth redirect."""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """GET /api/auth/google/callback — handle Google's redirect and resolve/create the account."""
    token    = oauth.google.authorize_access_token()
    userinfo = token['userinfo']
    return _handle_oauth(
        provider='google',
        provider_id=userinfo['sub'],
        email=userinfo['email'],
        display_name=userinfo.get('name', userinfo['email']),
    )


# ---- Microsoft OAuth ---------------------------------------------------------

@auth_bp.route('/microsoft')
def microsoft_login():
    """GET /api/auth/microsoft — kick off the Microsoft OAuth redirect."""
    redirect_uri = url_for('auth.microsoft_callback', _external=True)
    return oauth.microsoft.authorize_redirect(redirect_uri)


@auth_bp.route('/microsoft/callback')
def microsoft_callback():
    """GET /api/auth/microsoft/callback — handle Microsoft's redirect and resolve/create the account."""
    token    = oauth.microsoft.authorize_access_token()
    userinfo = oauth.microsoft.userinfo()
    return _handle_oauth(
        provider='microsoft',
        provider_id=userinfo['sub'],
        email=userinfo['email'],
        display_name=userinfo.get('name', userinfo['email']),
    )


# ---- OAuth registration completion ------------------------------------------
# Called by the frontend after an OAuth login with no existing account.
# Frontend collects starting_balance and state, then posts everything here.

@auth_bp.route('/oauth/register', methods=['POST'])
def oauth_register():
    """POST /api/auth/oauth/register — finalize a new account after first OAuth login.

    Validates the slider-chosen starting_balance is within bounds, then creates the user.
    """
    data            = request.get_json()
    provider        = data.get('provider')
    provider_id     = data.get('provider_id')
    email           = data.get('email')
    display_name    = data.get('display_name')
    state           = data.get('state')
    starting_balance = data.get('starting_balance')

    if not all([provider, provider_id, email, display_name, state, starting_balance]):
        return jsonify({'error': 'Missing required fields'}), 400

    if provider not in ('google', 'microsoft'):
        return jsonify({'error': 'Invalid provider'}), 400

    try:
        starting_balance = float(starting_balance)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid starting balance'}), 400

    if not (BALANCE_MIN <= starting_balance <= BALANCE_MAX):
        return jsonify({'error': f'Starting balance must be between {BALANCE_MIN} and {BALANCE_MAX}'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        email=email,
        display_name=display_name,
        state=state,
        starting_balance=starting_balance,
        balance=starting_balance,
        **{f'{provider}_id': provider_id},
    )
    db.session.add(user)
    db.session.commit()

    token = create_session_token(user.id)
    return jsonify({'user_id': user.id, 'token': token}), 201


# ---- Discord account linking -------------------------------------------------
# Bot calls /discord/link-token with the user's Discord ID to get a one-time URL.
# The logged-in website user opens that URL and calls /discord/link/complete with just the
# token — their identity comes from their session, never from a client-supplied user_id.

@auth_bp.route('/discord/link-token', methods=['POST'])
@require_bot
def discord_link_token():
    """POST /api/auth/discord/link-token — bot-only; mint a 15-min one-time link URL for a Discord ID."""
    discord_id = request.get_json().get('discord_id')
    if not discord_id:
        return jsonify({'error': 'Missing discord_id'}), 400

    token = secrets.token_urlsafe(24)
    _discord_link_tokens[token] = {
        'discord_id': discord_id,
        'expires_at': datetime.utcnow() + timedelta(minutes=15),
    }
    # Points at the frontend, not the backend directly — /discord/link/complete is POST-only and
    # the user needs a page to log in (if needed) and fire that POST from their session.
    link_url = f"{current_app.config['FRONTEND_URL']}/discord/link?token={token}"
    return jsonify({'url': link_url})


@auth_bp.route('/discord/link/complete', methods=['POST'])
@require_session
def discord_link_complete():
    """POST /api/auth/discord/link/complete — redeem a link token and attach discord_id to the
    logged-in user (g.user, from the session token — never a client-supplied id)."""
    token = (request.get_json() or {}).get('token')

    if not token:
        return jsonify({'error': 'Missing token'}), 400

    entry = _discord_link_tokens.get(token)
    if not entry or datetime.utcnow() > entry['expires_at']:
        _discord_link_tokens.pop(token, None)
        return jsonify({'error': 'Invalid or expired token'}), 400

    g.user.discord_id = entry['discord_id']
    db.session.commit()
    _discord_link_tokens.pop(token)

    return jsonify({'message': 'Discord account linked'})


# ---- Helpers -----------------------------------------------------------------

def _handle_oauth(provider: str, provider_id: str, email: str, display_name: str):
    """Resolve an OAuth login to a user and redirect back to the frontend with the result.

    Redirects to FRONTEND_URL/auth/callback with either ?token=... (a fresh session token for a
    known account) or ?requires_registration=1&... (new account — the frontend collects
    starting_balance/state and calls /oauth/register, which returns its own token).
    """
    id_field = f'{provider}_id'

    user = User.query.filter_by(**{id_field: provider_id}).first()

    if not user:
        # Link to an existing account if the email matches a different provider
        user = User.query.filter_by(email=email).first()
        if user:
            setattr(user, id_field, provider_id)
            db.session.commit()
        else:
            # New user — frontend must collect starting_balance and state
            params = urlencode({
                'requires_registration': '1',
                'provider':     provider,
                'provider_id':  provider_id,
                'email':        email,
                'display_name': display_name,
            })
            return redirect(f"{current_app.config['FRONTEND_URL']}/auth/callback?{params}")

    params = urlencode({'token': create_session_token(user.id)})
    return redirect(f"{current_app.config['FRONTEND_URL']}/auth/callback?{params}")
