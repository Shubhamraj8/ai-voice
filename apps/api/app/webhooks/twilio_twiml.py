"""TwiML builders for Twilio voice webhooks (ticket 2.02)."""

from xml.sax.saxutils import escape

from app.config import Settings

# Consent disclosure spoken before the AI agent connects (ticket 2.17).
# English, ~3s when spoken. DPDP §6 (notice of processing) sanity-check: states
# the call is recorded and AI-assisted before any capture begins. Tenants in
# other markets can override the wording (ticket 5.14); a legal pre-clearance of
# the standard line is tracked for the v1.5 review.
CONSENT_DISCLOSURE_TEXT = "This call may be recorded for quality and AI assistance."


def effective_disclosure(override: str | None) -> str:
    """The tenant's disclosure override, or the standard line (ticket 5.14)."""
    text = (override or "").strip()
    return text or CONSENT_DISCLOSURE_TEXT


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


NOT_CONFIGURED_MESSAGE = "Sorry, this number is not configured for service. Goodbye."


def build_not_configured_twiml(message: str = NOT_CONFIGURED_MESSAGE) -> str:
    """TwiML for an inbound call to a number with no active agent (ticket 3.09)."""
    safe = escape(message)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Say>{safe}</Say>"
        "<Hangup/>"
        "</Response>"
    )


def build_voice_connect_twiml(
    stream_url: str,
    *,
    disclosure_text: str = CONSENT_DISCLOSURE_TEXT,
) -> str:
    safe_url = escape(stream_url, {'"': "&quot;"})
    safe_disclosure = escape(disclosure_text)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        # Consent disclosure plays first, before the media stream connects.
        f"<Say>{safe_disclosure}</Say>"
        "<Connect>"
        f'<Stream url="{safe_url}" />'
        "</Connect>"
        "</Response>"
    )
