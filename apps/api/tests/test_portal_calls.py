"""Tests for the tenant call history list (ticket 5.09). DB mocked."""

import uuid
from datetime import UTC, datetime

from app.services import portal_calls as pc


def _row(**over):
    base = {
        "id": uuid.uuid4(),
        "from_number": "+919876543210",
        "started_at": datetime(2026, 6, 18, tzinfo=UTC),
        "duration_secs": 120,
        "outcome": "booked",
        "intent": "appointment",
        "summary": "Booked a slot",
    }
    base.update(over)
    return base


async def test_list_calls_no_filters(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pc, "get_pool", lambda: pool)
    tid = uuid.uuid4()
    conn.fetchval.return_value = 3
    conn.fetch.side_effect = [
        [_row(), _row()],  # page rows
        [{"intent": "appointment"}, {"intent": "support"}],  # distinct intents
    ]

    result = await pc.list_tenant_calls(tid, page=1, page_size=25)

    assert result.total == 3
    assert len(result.items) == 2
    assert result.available_intents == ["appointment", "support"]
    # rows query: tenant + limit + offset only (no filters)
    rows_params = conn.fetch.await_args_list[0].args[1:]
    assert rows_params == (tid, 25, 0)


async def test_list_calls_with_filters(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(pc, "get_pool", lambda: pool)
    tid = uuid.uuid4()
    conn.fetchval.return_value = 1
    conn.fetch.side_effect = [[_row()], []]

    result = await pc.list_tenant_calls(
        tid,
        page=2,
        page_size=10,
        outcome="booked",
        search="98765",
    )

    rows_call = conn.fetch.await_args_list[0]
    sql = rows_call.args[0]
    params = rows_call.args[1:]
    assert "outcome = $2" in sql
    assert "from_number ILIKE" in sql and "summary ILIKE" in sql
    # tenant, outcome, search-like, limit, offset(=10 for page 2)
    assert params == (tid, "booked", "%98765%", 10, 10)
    assert result.page == 2
