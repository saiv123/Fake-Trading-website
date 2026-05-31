# Thin requests wrapper for the bot — attaches the base URL and BOT_API_KEY, plus the caller's Discord ID
# (X-Discord-Id) so Flask resolves which linked user is acting. Commands call these from a thread (asyncio.to_thread)
# so the blocking requests calls don't stall the event loop.
import os
import requests

_BASE_URL = os.environ["FLASK_API_BASE_URL"].rstrip("/")
_API_KEY = os.environ["BOT_API_KEY"]


def _headers(discord_id=None) -> dict:
    headers = {"X-API-Key": _API_KEY}
    if discord_id is not None:
        headers["X-Discord-Id"] = str(discord_id)
    return headers


def get(path: str, discord_id=None, **kwargs) -> requests.Response:
    return requests.get(f"{_BASE_URL}{path}", headers=_headers(discord_id), timeout=15, **kwargs)


def post(path: str, discord_id=None, **kwargs) -> requests.Response:
    return requests.post(f"{_BASE_URL}{path}", headers=_headers(discord_id), timeout=15, **kwargs)


def patch(path: str, discord_id=None, **kwargs) -> requests.Response:
    return requests.patch(f"{_BASE_URL}{path}", headers=_headers(discord_id), timeout=15, **kwargs)


def delete(path: str, discord_id=None, **kwargs) -> requests.Response:
    return requests.delete(f"{_BASE_URL}{path}", headers=_headers(discord_id), timeout=15, **kwargs)
