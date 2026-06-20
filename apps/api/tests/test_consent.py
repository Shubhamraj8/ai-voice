"""Tests for per-tenant consent disclosure (ticket 5.14). DB mocked."""

import uuid

from app.services import call_routing, consent
from app.webhooks.twilio_twiml import (
    CONSENT_DISCLOSURE_TEXT,
    build_voice_connect_twiml,
    effective_disclosure,
)


def test_effective_disclosure_falls_back_to_default():
    assert effective_disclosure(None) == CONSENT_DISCLOSURE_TEXT
    assert effective_disclosure("   ") == CONSENT_DISCLOSURE_TEXT
    assert effective_disclosure("Llamada grabada.") == "Llamada grabada."


def test_disclosure_is_spoken_before_audio_capture():
    """Consent must precede recording: the <Say> disclosure has to come before
    the <Connect><Stream> that opens the media (audio capture) channel."""

    twiml = build_voice_connect_twiml("ws://x/media", disclosure_text="Custom notice.")

    assert "<Say>Custom notice.</Say>" in twiml
    assert twiml.index("<Say>") < twiml.index("<Connect>") < twiml.index("<Stream")


async def test_resolve_carries_consent_override(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(call_routing, "get_pool", lambda: pool)
    conn.fetchrow.return_value = {
        "agent_id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "stt": "deepgram",
        "tts": "deepgram",
        "llm": "deepseek_native",
        "consent_disclosure_text": "Esta llamada será grabada.",
    }

    route = await call_routing.resolve_agent_by_number("+911234567890")

    assert route.consent_disclosure_text == "Esta llamada será grabada."


async def test_get_consent_disclosure_custom(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(consent, "get_pool", lambda: pool)
    conn.fetchval.return_value = "Esta llamada será grabada."

    result = await consent.get_consent_disclosure(uuid.uuid4())

    assert result.is_custom is True
    assert result.text == "Esta llamada será grabada."
    assert result.default_text == CONSENT_DISCLOSURE_TEXT


async def test_get_consent_disclosure_default(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(consent, "get_pool", lambda: pool)
    conn.fetchval.return_value = None

    result = await consent.get_consent_disclosure(uuid.uuid4())

    assert result.is_custom is False
    assert result.text == CONSENT_DISCLOSURE_TEXT
