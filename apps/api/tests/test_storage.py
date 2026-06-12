"""Unit tests for the Supabase Storage client (ticket 2.14). No real network."""

from types import SimpleNamespace

from app.services import storage


def _fake_settings():
    return SimpleNamespace(
        supabase_url="https://proj.supabase.co",
        supabase_service_role_key="svc-key",
        recordings_bucket="recordings",
        recording_signed_url_ttl_s=3600,
    )


class _FakeResponse:
    def __init__(self, *, json_data=None, content=b"", status_code=200):
        self._json = json_data
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


def _client_factory(recorder, response, *, raise_on_call=False):
    class _FakeClient:
        def __init__(self, **kwargs):
            recorder["init"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, **kwargs):
            recorder["post"] = {"url": url, **kwargs}
            if raise_on_call:
                raise RuntimeError("boom")
            return response

    return _FakeClient


async def test_upload_recording_posts_to_object_endpoint(monkeypatch):
    monkeypatch.setattr(storage, "get_settings", _fake_settings)
    rec = {}
    monkeypatch.setattr(
        storage.httpx, "AsyncClient", _client_factory(rec, _FakeResponse())
    )

    ok = await storage.upload_recording(path="tenant/call.mp3", data=b"abc")

    assert ok is True
    assert rec["post"]["url"] == (
        "https://proj.supabase.co/storage/v1/object/recordings/tenant/call.mp3"
    )
    assert rec["post"]["content"] == b"abc"
    headers = rec["post"]["headers"]
    assert headers["Authorization"] == "Bearer svc-key"
    assert headers["x-upsert"] == "true"


async def test_upload_recording_returns_false_on_error(monkeypatch):
    monkeypatch.setattr(storage, "get_settings", _fake_settings)
    rec = {}
    monkeypatch.setattr(
        storage.httpx,
        "AsyncClient",
        _client_factory(rec, _FakeResponse(), raise_on_call=True),
    )

    assert await storage.upload_recording(path="t/c.mp3", data=b"x") is False


async def test_create_signed_url_returns_full_url(monkeypatch):
    monkeypatch.setattr(storage, "get_settings", _fake_settings)
    rec = {}
    resp = _FakeResponse(
        json_data={"signedURL": "/object/sign/recordings/tenant/call.mp3?token=xyz"}
    )
    monkeypatch.setattr(storage.httpx, "AsyncClient", _client_factory(rec, resp))

    url = await storage.create_signed_url(path="tenant/call.mp3")

    assert url == (
        "https://proj.supabase.co/storage/v1"
        "/object/sign/recordings/tenant/call.mp3?token=xyz"
    )
    assert rec["post"]["json"] == {"expiresIn": 3600}
