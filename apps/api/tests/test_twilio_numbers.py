"""Unit tests for Twilio number provisioning (ticket 3.06). No real Twilio."""

from types import SimpleNamespace

from app.services import twilio_numbers


class _FakeLocal:
    def __init__(self, numbers):
        self._numbers = numbers

    def list(self, limit):
        return self._numbers[:limit]


class _FakeAvailable:
    def __init__(self, numbers):
        self.local = _FakeLocal(numbers)


class _FakeIncomingCtx:
    def __init__(self, recorder):
        self._rec = recorder

    def update(self, **kwargs):
        self._rec["update"] = kwargs

    def delete(self):
        self._rec["deleted"] = True


class _FakeIncoming:
    def __init__(self, recorder):
        self._rec = recorder

    def create(self, phone_number):
        self._rec["created"] = phone_number
        return SimpleNamespace(sid="PN123")

    def __call__(self, sid):
        self._rec["sid"] = sid
        return _FakeIncomingCtx(self._rec)


class _FakeClient:
    def __init__(self, numbers, recorder):
        self._numbers = numbers
        self._rec = recorder

    def available_phone_numbers(self, region):
        self._rec["region"] = region
        return _FakeAvailable(self._numbers)

    @property
    def incoming_phone_numbers(self):
        return _FakeIncoming(self._rec)


def _patch_settings(monkeypatch):
    monkeypatch.setattr(
        twilio_numbers,
        "get_settings",
        lambda: SimpleNamespace(public_api_base_url="https://api.example.com"),
    )


async def test_search_available_numbers(monkeypatch):
    rec = {}
    nums = [
        SimpleNamespace(
            phone_number="+911111111111",
            friendly_name="+911111111111",
            locality="Mumbai",
            region="MH",
        ),
        SimpleNamespace(
            phone_number="+912222222222",
            friendly_name="+912222222222",
            locality="Delhi",
            region="DL",
        ),
    ]
    monkeypatch.setattr(twilio_numbers, "_client", lambda: _FakeClient(nums, rec))

    result = await twilio_numbers.search_available_numbers(region="IN", limit=5)

    assert rec["region"] == "IN"
    assert result[0]["phone_number"] == "+911111111111"
    assert result[0]["locality"] == "Mumbai"
    assert len(result) == 2


async def test_purchase_number_returns_sid(monkeypatch):
    rec = {}
    monkeypatch.setattr(twilio_numbers, "_client", lambda: _FakeClient([], rec))

    sid = await twilio_numbers.purchase_number("+911111111111")

    assert sid == "PN123"
    assert rec["created"] == "+911111111111"


async def test_configure_voice_webhook_sets_urls(monkeypatch):
    rec = {}
    monkeypatch.setattr(twilio_numbers, "_client", lambda: _FakeClient([], rec))
    _patch_settings(monkeypatch)

    await twilio_numbers.configure_voice_webhook("PN123")

    assert rec["sid"] == "PN123"
    assert rec["update"]["voice_url"] == "https://api.example.com/webhooks/twilio/voice"
    assert (
        rec["update"]["status_callback"]
        == "https://api.example.com/webhooks/twilio/status"
    )


async def test_release_number_deletes(monkeypatch):
    rec = {}
    monkeypatch.setattr(twilio_numbers, "_client", lambda: _FakeClient([], rec))

    await twilio_numbers.release_number("PN123")

    assert rec["deleted"] is True
