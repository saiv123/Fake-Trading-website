"""User account model.

One row per registered user. Accounts are created via Google/Microsoft OAuth (no passwords),
optionally linked to a Discord ID later. `starting_balance`/`balance` use DECIMAL for exact money
math, and `state` drives the tax calculation. MFA columns are reserved for V2.
"""
from datetime import datetime
from .. import db


class User(db.Model):
    """A registered trader: identity, OAuth/Discord links, paper-cash balance, and tax state."""

    __tablename__ = 'users'

    id               = db.Column(db.Integer, primary_key=True)
    email            = db.Column(db.String(255), unique=True, nullable=False)
    display_name     = db.Column(db.String(100), nullable=False)

    # OAuth provider IDs — at least one must be set
    google_id        = db.Column(db.String(255), unique=True)
    microsoft_id     = db.Column(db.String(255), unique=True)
    discord_id       = db.Column(db.String(255), unique=True)  # set after /link in Discord

    # starting_balance and balance are immutable after creation — routes enforce 403 on any PUT
    # starting_balance is whatever the user set on the slider at registration (preset or custom)
    starting_balance = db.Column(db.Numeric(15, 2), nullable=False)
    balance          = db.Column(db.Numeric(15, 2), nullable=False)

    state            = db.Column(db.String(2), nullable=False)  # two-letter US state for tax calc
    last_active_at   = db.Column(db.DateTime)
    drip_all         = db.Column(db.Boolean, default=False, nullable=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # V2 — MFA via TOTP; mfa_secret stored encrypted at rest
    mfa_enabled      = db.Column(db.Boolean, default=False, nullable=False)
    mfa_secret       = db.Column(db.String(255))

