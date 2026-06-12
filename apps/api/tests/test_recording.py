"""Unit tests for the recording capture/storage service (ticket 2.14).

Everything external (Twilio download, Supabase upload, DB) is mocked.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.services import recording


def _settings():
    return SimpleNamespace(
        recordings_bucket="recordings",
        twilio_account_sid="AC",
        twilio_auth_token="tok",
        public_api_base_url="https://api.example.com",
        twilio_recording_status_path="/webhooks/twilio/recording",
    )


def test_recording_status_callback_url_joins_base_and_path():
    settings = SimpleNamespace(
        public_api_base_url="https://api.example.com/",
        twilio_recording_status_path="/webhooks/twilio/recording",
    )
    assert (
        recording.recording_status_callback_url(settings)
        == "https://api.example.com/webhooks/twilio/recording"
    )


def test_start_call_recording_skips_without_credentials():
    settings = SimpleNamespace(
        twilio_account_sid="",
        twilio_auth_token="",
        public_api_base_url="https://api.example.com",
        twilio_recording_status_path="/webhooks/twilio/recording",
    )
    # No credentials -> returns without raising and without a Twilio call.
    recording.start_call_recording("CA1", settings)


async def test_process_recording_uploads_and_sets_url(monkeypatch):
    call_id = uuid.uuid4()
    monkeypatch.setattr(recording, "get_settings", _settings)
    monkeypatch.setattr(
        recording, "get_call_id_by_sid", AsyncMock(return_value=call_id)
    )
    monkeypatch.setattr(
        recording, "_download_twilio_recording", AsyncMock(return_value=b"audio")
    )
    upload = AsyncMock(return_value=True)
    monkeypatch.setattr(recording, "upload_recording", upload)
    set_url = AsyncMock()
    monkeypatch.setattr(recording, "set_recording_url", set_url)

    await recording.process_recording("CA1", "https://api.twilio.com/RE1")

    object_path = f"{recording.DEV_TENANT_ID}/{call_id}.mp3"
    upload.assert_awaited_once_with(path=object_path, data=b"audio")
    set_url.assert_awaited_once_with(
        twilio_call_sid="CA1", path=f"recordings/{object_path}"
    )


async def test_process_recording_skips_when_no_call(monkeypatch):
    monkeypatch.setattr(recording, "get_settings", _settings)
    monkeypatch.setattr(recording, "get_call_id_by_sid", AsyncMock(return_value=None))
    upload = AsyncMock()
    monkeypatch.setattr(recording, "upload_recording", upload)

    await recording.process_recording("CA1", "url")
    upload.assert_not_awaited()


async def test_process_recording_skips_db_update_when_upload_fails(monkeypatch):
    monkeypatch.setattr(recording, "get_settings", _settings)
    monkeypatch.setattr(
        recording, "get_call_id_by_sid", AsyncMock(return_value=uuid.uuid4())
    )
    monkeypatch.setattr(
        recording, "_download_twilio_recording", AsyncMock(return_value=b"a")
    )
    monkeypatch.setattr(recording, "upload_recording", AsyncMock(return_value=False))
    set_url = AsyncMock()
    monkeypatch.setattr(recording, "set_recording_url", set_url)

    await recording.process_recording("CA1", "url")
    set_url.assert_not_awaited()


async def test_download_appends_mp3_suffix(monkeypatch):
    settings = SimpleNamespace(twilio_account_sid="AC", twilio_auth_token="tok")
    rec = {}

    class _Resp:
        content = b"audio"

        def raise_for_status(self):
            pass

    class _FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url, **kwargs):
            rec["url"] = url
            return _Resp()

    monkeypatch.setattr(recording.httpx, "AsyncClient", _FakeClient)

    data = await recording._download_twilio_recording("https://api/RE1", settings)
    assert data == b"audio"
    assert rec["url"] == "https://api/RE1.mp3"
