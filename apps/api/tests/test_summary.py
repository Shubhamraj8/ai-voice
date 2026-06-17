"""Tests for the post-call summary job (ticket 4.13). DeepSeek + DB mocked."""

import uuid
from unittest.mock import AsyncMock

from app.services import summary as summ


def _msgs():
    return [
        {"role": "user", "content": "hi, what are your hours?"},
        {"role": "assistant", "content": "we are open 9 to 5"},
    ]


def _setup(monkeypatch, pool, *, fetch=None, complete=None):
    monkeypatch.setattr(summ, "get_pool", lambda: pool)
    if complete is not None:
        monkeypatch.setattr(summ, "_complete_json", complete)
    return pool


# --- helpers -----------------------------------------------------------------


def test_truncate_words():
    assert summ._truncate_words("a b c", limit=80) == "a b c"
    out = summ._truncate_words("w " * 100, limit=80)
    assert out.endswith("…") and len(out.split()) == 80  # 80 words; ellipsis on last


# --- generate_call_summary ---------------------------------------------------


async def test_success_writes_summary(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = _msgs()
    complete = AsyncMock(
        return_value={
            "summary": "Asked hours.",
            "intent": "hours",
            "outcome": "resolved",
        }
    )
    _setup(monkeypatch, pool, complete=complete)
    call_id = uuid.uuid4()

    await summ.generate_call_summary(call_id)

    # transcript was built from the turns
    assert "Caller: hi" in complete.await_args.args[0]
    conn.execute.assert_awaited_once()
    args = conn.execute.await_args.args
    assert args[1] == call_id
    assert args[2] == "Asked hours."
    assert args[3] == "hours"
    assert args[4] == "resolved"


async def test_empty_transcript_skips(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = []
    complete = AsyncMock()
    _setup(monkeypatch, pool, complete=complete)

    await summ.generate_call_summary(uuid.uuid4())

    complete.assert_not_awaited()
    conn.execute.assert_not_awaited()


async def test_invalid_outcome_becomes_other(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = _msgs()
    _setup(
        monkeypatch,
        pool,
        complete=AsyncMock(
            return_value={"summary": "S", "intent": "x", "outcome": "weird"}
        ),
    )

    await summ.generate_call_summary(uuid.uuid4())

    assert conn.execute.await_args.args[4] == "other"


async def test_retry_then_success(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = _msgs()
    complete = AsyncMock(
        side_effect=[
            RuntimeError("boom"),
            {"summary": "S", "intent": "x", "outcome": "resolved"},
        ]
    )
    _setup(monkeypatch, pool, complete=complete)

    await summ.generate_call_summary(uuid.uuid4())

    assert complete.await_count == 2
    assert conn.execute.await_args.args[4] == "resolved"


async def test_persistent_failure_writes_unclassified(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetch.return_value = _msgs()
    _setup(monkeypatch, pool, complete=AsyncMock(side_effect=RuntimeError("down")))

    await summ.generate_call_summary(uuid.uuid4())

    args = conn.execute.await_args.args
    assert args[2] is None  # summary
    assert args[3] == "unclassified"  # intent
    assert args[4] is None  # outcome (preserved via COALESCE)
