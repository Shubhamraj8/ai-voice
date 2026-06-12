import pytest
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

AUTH_TOKEN = "test-twilio-auth-token"
VOICE_URL = "http://testserver/webhooks/twilio/voice"
STATUS_URL = "http://testserver/webhooks/twilio/status"

VOICE_PARAMS = {
    "CallSid": "CA1234567890abcdef",
    "From": "+15551234567",
    "To": "+919876543210",
    "CallStatus": "ringing",
    "Direction": "inbound",
}

STATUS_PARAMS = {
    "CallSid": "CA1234567890abcdef",
    "CallStatus": "completed",
    "CallDuration": "42",
    "From": "+15551234567",
    "To": "+919876543210",
}

RECORDING_URL = "http://testserver/webhooks/twilio/recording"

RECORDING_PARAMS = {
    "CallSid": "CA1234567890abcdef",
    "RecordingSid": "RE1234567890abcdef",
    "RecordingStatus": "completed",
    "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC/Recordings/RE1",
}

client = TestClient(app)


@pytest.fixture
def twilio_env(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", AUTH_TOKEN)
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "http://testserver")
    monkeypatch.setenv("TWILIO_SIGNATURE_VALIDATION", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _sign(url: str, params: dict[str, str]) -> str:
    return RequestValidator(AUTH_TOKEN).compute_signature(url, params)


def test_voice_webhook_returns_connect_stream_twiml(twilio_env):
    signature = _sign(VOICE_URL, VOICE_PARAMS)
    response = client.post(
        "/webhooks/twilio/voice",
        data=VOICE_PARAMS,
        headers={"X-Twilio-Signature": signature},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    body = response.text
    assert '<?xml version="1.0" encoding="UTF-8"?>' in body
    assert "<Response>" in body
    assert "<Connect>" in body
    assert '<Stream url="ws://testserver/webhooks/twilio/media" />' in body


def test_voice_webhook_rejects_missing_signature(twilio_env):
    response = client.post("/webhooks/twilio/voice", data=VOICE_PARAMS)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "twilio_signature_missing"


def test_voice_webhook_rejects_invalid_signature(twilio_env):
    response = client.post(
        "/webhooks/twilio/voice",
        data=VOICE_PARAMS,
        headers={"X-Twilio-Signature": "invalid"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "twilio_signature_invalid"


def test_status_webhook_accepts_valid_signature(twilio_env):
    signature = _sign(STATUS_URL, STATUS_PARAMS)
    response = client.post(
        "/webhooks/twilio/status",
        data=STATUS_PARAMS,
        headers={"X-Twilio-Signature": signature},
    )

    assert response.status_code == 204
    assert response.text == ""


def test_status_webhook_rejects_invalid_signature(twilio_env):
    response = client.post(
        "/webhooks/twilio/status",
        data=STATUS_PARAMS,
        headers={"X-Twilio-Signature": "invalid"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "twilio_signature_invalid"


def test_build_media_stream_url_uses_wss_for_https(twilio_env, monkeypatch):
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://ai-voice-ocy9.onrender.com")
    get_settings.cache_clear()

    signature = RequestValidator(AUTH_TOKEN).compute_signature(
        "https://ai-voice-ocy9.onrender.com/webhooks/twilio/voice",
        VOICE_PARAMS,
    )
    response = client.post(
        "/webhooks/twilio/voice",
        data=VOICE_PARAMS,
        headers={"X-Twilio-Signature": signature},
    )

    assert response.status_code == 200
    assert (
        '<Stream url="wss://ai-voice-ocy9.onrender.com/webhooks/twilio/media" />'
        in response.text
    )
    get_settings.cache_clear()


def test_recording_webhook_schedules_processing(twilio_env, monkeypatch):
    captured = {}

    def fake_process(call_sid, recording_url):
        captured["args"] = (call_sid, recording_url)

    monkeypatch.setattr("app.routes.twilio_webhooks.process_recording", fake_process)

    signature = _sign(RECORDING_URL, RECORDING_PARAMS)
    response = client.post(
        "/webhooks/twilio/recording",
        data=RECORDING_PARAMS,
        headers={"X-Twilio-Signature": signature},
    )

    assert response.status_code == 204
    assert captured["args"] == (
        RECORDING_PARAMS["CallSid"],
        RECORDING_PARAMS["RecordingUrl"],
    )


def test_recording_webhook_rejects_invalid_signature(twilio_env):
    response = client.post(
        "/webhooks/twilio/recording",
        data=RECORDING_PARAMS,
        headers={"X-Twilio-Signature": "invalid"},
    )

    assert response.status_code == 403
