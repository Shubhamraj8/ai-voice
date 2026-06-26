"""Unit tests for the call-lifecycle persistence service (ticket 2.13).

The database is fully mocked — no pipeline, network, or real Postgres.
"""

import uuid
from types import SimpleNamespace

from app.services import calls


def _settings(*, deepgram: str = "", deepseek: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        deepgram_api_key=deepgram,
        deepseek_api_key=deepseek,
        llm_provider="deepseek",
        gemini_api_key="",
    )


# --- build_provider_snapshot -------------------------------------------------


def test_provider_snapshot_full_pipeline():
    snap = calls.build_provider_snapshot(_settings(deepgram="dg", deepseek="ds"))
    assert snap == {"stt": "deepgram", "tts": "deepgram", "llm": "deepseek_native"}


def test_provider_snapshot_deepgram_only_has_no_llm():
    snap = calls.build_provider_snapshot(_settings(deepgram="dg"))
    assert snap == {"stt": "deepgram", "tts": "deepgram", "llm": None}


def test_provider_snapshot_no_providers():
    snap = calls.build_provider_snapshot(_settings())
    assert snap == {"stt": None, "tts": None, "llm": None}


# --- start_call --------------------------------------------------------------


async def test_start_call_returns_id(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    expected = uuid.uuid4()
    conn.fetchval.return_value = expected
    monkeypatch.setattr(calls, "get_pool", lambda: pool)

    result = await calls.start_call(
        twilio_call_sid="CA123",
        from_number="+15551234567",
        provider_snapshot={"stt": "deepgram", "tts": "deepgram", "llm": None},
    )

    assert result == expected
    conn.fetchval.assert_awaited_once()
    args = conn.fetchval.await_args.args
    assert args[1] == calls.DEV_TENANT_ID
    assert args[2] == calls.DEV_AGENT_ID
    assert args[3] == "CA123"
    assert args[4] == "+15551234567"


async def test_start_call_swallows_db_error(monkeypatch):
    def _boom():
        raise RuntimeError("pool not initialized")

    monkeypatch.setattr(calls, "get_pool", _boom)

    result = await calls.start_call(
        twilio_call_sid="CA123",
        from_number="+1",
        provider_snapshot={},
    )

    assert result is None


# --- get_call_id_by_sid ------------------------------------------------------


async def test_get_call_id_by_sid(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    expected = uuid.uuid4()
    conn.fetchval.return_value = expected
    monkeypatch.setattr(calls, "get_pool", lambda: pool)

    assert await calls.get_call_id_by_sid("CA123") == expected


# --- record_turn -------------------------------------------------------------


async def test_record_turn_inserts_assistant_row(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(calls, "get_pool", lambda: pool)
    call_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    await calls.record_turn(
        call_id=call_id,
        tenant_id=tenant_id,
        role="assistant",
        content="Hello there",
        latency_ms=850,
        tts_chars=11,
    )

    conn.execute.assert_awaited_once()
    args = conn.execute.await_args.args
    assert args[1] == call_id
    assert args[2] == tenant_id
    assert args[3] == "assistant"
    assert args[4] == "Hello there"
    assert args[5] == 850
    assert args[6] == 11


async def test_record_turn_defaults_tenant_when_none(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(calls, "get_pool", lambda: pool)

    await calls.record_turn(
        call_id=uuid.uuid4(),
        tenant_id=None,
        role="user",
        content="hi",
    )

    args = conn.execute.await_args.args
    assert args[2] == calls.DEV_TENANT_ID


async def test_record_turn_persists_latency_breakdown(mock_db_pool, monkeypatch):
    import json

    pool, conn = mock_db_pool
    monkeypatch.setattr(calls, "get_pool", lambda: pool)
    breakdown = {
        "stt_ms": 100,
        "llm_ms": 300,
        "tts_first_byte_ms": 200,
        "total_ms": 700,
    }

    await calls.record_turn(
        call_id=uuid.uuid4(),
        role="assistant",
        content="hi",
        latency_ms=700,
        latency_breakdown=breakdown,
    )

    args = conn.execute.await_args.args
    assert json.loads(args[7]) == breakdown


# --- end_call ----------------------------------------------------------------


async def test_end_call_returns_id(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    expected = uuid.uuid4()
    conn.fetchval.return_value = expected
    monkeypatch.setattr(calls, "get_pool", lambda: pool)

    result = await calls.end_call(twilio_call_sid="CA123", duration_secs=42)

    assert result == expected
    args = conn.fetchval.await_args.args
    assert args[1] == "CA123"
    assert args[2] == 42


async def test_end_call_noop_when_already_closed(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchval.return_value = None
    monkeypatch.setattr(calls, "get_pool", lambda: pool)

    assert await calls.end_call(twilio_call_sid="CA123") is None


# --- close_stale_calls -------------------------------------------------------


async def test_close_stale_calls_returns_count(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = [{"id": uuid.uuid4()}, {"id": uuid.uuid4()}]
    monkeypatch.setattr(calls, "get_pool", lambda: pool)

    closed = await calls.close_stale_calls(max_age_seconds=3600)

    assert closed == 2
    args = conn.fetch.await_args.args
    assert args[1] == 3600


async def test_close_stale_calls_swallows_error(monkeypatch):
    def _boom():
        raise RuntimeError("no pool")

    monkeypatch.setattr(calls, "get_pool", _boom)

    assert await calls.close_stale_calls(max_age_seconds=3600) == 0


# --- set_recording_url (ticket 2.14) -----------------------------------------


async def test_set_recording_url_updates_row(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(calls, "get_pool", lambda: pool)

    await calls.set_recording_url(
        twilio_call_sid="CA123", path="recordings/tenant/call.mp3"
    )

    conn.execute.assert_awaited_once()
    args = conn.execute.await_args.args
    assert args[1] == "CA123"
    assert args[2] == "recordings/tenant/call.mp3"
