"""Tests for 30-day recording retention (ticket 5.15). DB + storage mocked."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from app.services import recording_retention as rr

IST = timezone(timedelta(hours=5, minutes=30))


def test_seconds_until_next_run_same_day():
    now = datetime(2026, 6, 19, 2, 0, tzinfo=IST)  # 02:00 IST → 03:00 today
    assert rr.seconds_until_next_run(now) == 3600


def test_seconds_until_next_run_next_day():
    now = datetime(2026, 6, 19, 4, 0, tzinfo=IST)  # 04:00 IST → 03:00 tomorrow
    assert rr.seconds_until_next_run(now) == 23 * 3600


async def test_purge_deletes_audio_and_nulls_url(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(rr, "get_pool", lambda: pool)
    conn.fetch.return_value = [
        {"id": uuid.uuid4(), "recording_url": "t/c1.mp3"},
        {"id": uuid.uuid4(), "recording_url": "t/c2.mp3"},
    ]
    delete = AsyncMock(return_value=True)
    monkeypatch.setattr(rr, "delete_recording", delete)
    audit = AsyncMock()
    monkeypatch.setattr(rr, "log_system_action", audit)

    count = await rr.purge_old_recordings()

    assert count == 2
    assert delete.await_count == 2
    # the WHERE selects only old recordings, with retention_days as a param
    select_sql = conn.fetch.await_args.args[0]
    assert "recording_url IS NOT NULL" in select_sql
    assert "ended_at < now() - make_interval(days => $1)" in select_sql
    assert conn.fetch.await_args.args[1] == 30
    # each row nulled + stamped
    assert conn.execute.await_count == 2
    update_sql = conn.execute.await_args.args[0]
    assert "recording_url = NULL" in update_sql
    assert "recording_deleted_at = now()" in update_sql
    # one batch audit row
    audit.assert_awaited_once()
    assert audit.await_args.kwargs["payload"]["count"] == 2


async def test_purge_idempotent_when_file_already_gone(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(rr, "get_pool", lambda: pool)
    conn.fetch.return_value = [{"id": uuid.uuid4(), "recording_url": "t/gone.mp3"}]
    # delete reports False (already deleted) — must not raise, still nulls the row
    monkeypatch.setattr(rr, "delete_recording", AsyncMock(return_value=False))
    monkeypatch.setattr(rr, "log_system_action", AsyncMock())

    count = await rr.purge_old_recordings()

    assert count == 1
    conn.execute.assert_awaited_once()


async def test_purge_no_old_recordings(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(rr, "get_pool", lambda: pool)
    conn.fetch.return_value = []
    audit = AsyncMock()
    monkeypatch.setattr(rr, "log_system_action", audit)
    monkeypatch.setattr(rr, "delete_recording", AsyncMock())

    assert await rr.purge_old_recordings() == 0
    audit.assert_not_awaited()
