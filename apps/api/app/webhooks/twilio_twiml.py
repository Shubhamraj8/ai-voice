"""TwiML builders for Twilio voice webhooks (ticket 2.02)."""

from xml.sax.saxutils import escape

from app.config import Settings


def build_media_stream_url(settings: Settings) -> str:
    """WebSocket URL for Twilio Media Streams (handler wired in ticket 2.04)."""
    base = settings.public_api_base_url.rstrip("/")
    if base.startswith("https://"):
        ws_base = "wss://" + base.removeprefix("https://")
    elif base.startswith("http://"):
        ws_base = "ws://" + base.removeprefix("http://")
    else:
        ws_base = base

    path = settings.twilio_media_stream_path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{ws_base.rstrip('/')}{path}"


def build_voice_connect_twiml(stream_url: str) -> str:
    safe_url = escape(stream_url, {'"': "&quot;"})
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Connect>"
        f'<Stream url="{safe_url}" />'
        "</Connect>"
        "</Response>"
    )
