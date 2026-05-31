# Shared helpers for command extensions — runs blocking API calls off the event loop and formats common errors.
import asyncio

GREEN = 0x2ECC71
RED   = 0xE74C3C
BLUE  = 0x3498DB
GREY  = 0x95A5A6


async def call(fn, *args, **kwargs):
    """Run a blocking api_client call in a worker thread so the Discord event loop stays responsive."""
    return await asyncio.to_thread(fn, *args, **kwargs)


def error_message(resp) -> str:
    if resp.status_code == 404:
        return "Your Discord isn't linked to a trading account yet — use `/link` first."
    try:
        return resp.json().get("error", "Something went wrong.")
    except Exception:
        return "Something went wrong."


def money(value) -> str:
    if value is None:
        return "—"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)
