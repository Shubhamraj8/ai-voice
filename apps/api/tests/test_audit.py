"""Unit tests for the audit-log write helpers (ticket 3.11). DB mocked."""

import json
import uuid

from app.services import audit


def test_redact_scrubs_sensitive_keys():
    result = audit._redact(
        {
            "api_key": "sk-123",
            "auth_token": "secret",
            "name": "Acme",
            "nested": {"password": "p", "ok": 1},
            "items": [{"card_number": "4111"}],
        }
    )

    assert result["api_key"] == "[REDACTED]"
    assert result["auth_token"] == "[REDACTED]"
    assert result["name"] == "Acme"
    assert result["nested"]["password"] == "[REDACTED]"
    assert result["nested"]["ok"] == 1
    assert result["items"][0]["card_number"] == "[REDACTED]"


async def test_log_internal_action_writes_internal_row(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(audit, "get_pool", lambda: pool)
    actor = uuid.uuid4()
    tenant = uuid.uuid4()
    target = uuid.uuid4()

    await audit.log_internal_action(
        actor,
        "internal.agent.update",
        tenant_id=tenant,
        target_type="agent",
        target_id=target,
        payload={"name": "New"},
    )

    args = conn.execute.await_args.args
    assert args[1] == actor
    assert args[2] == "internal_user"
    assert args[3] == "internal.agent.update"
    assert args[4] == "agent"
    assert args[5] == target
    assert json.loads(args[6]) == {"name": "New"}
    assert args[7] == tenant


async def test_log_internal_action_redacts_payload(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(audit, "get_pool", lambda: pool)

    await audit.log_internal_action(
        uuid.uuid4(), "x", payload={"api_key": "sk-secret", "name": "ok"}
    )

    stored = json.loads(conn.execute.await_args.args[6])
    assert stored["api_key"] == "[REDACTED]"
    assert stored["name"] == "ok"


async def test_log_system_action_uses_system_actor(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(audit, "get_pool", lambda: pool)

    await audit.log_system_action("ingest.run", payload={"count": 3})

    args = conn.execute.await_args.args
    assert args[1] is None
    assert args[2] == "system"
    assert args[3] == "ingest.run"


async def test_audit_swallows_db_error(monkeypatch):
    def _boom():
        raise RuntimeError("no pool")

    monkeypatch.setattr(audit, "get_pool", _boom)
    # Must not raise.
    await audit.log_internal_action(uuid.uuid4(), "x", payload={"a": 1})
