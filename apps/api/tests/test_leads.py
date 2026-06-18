"""Tests for lead capture (ticket 5.02). DB + email mocked, no pipecat import."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.models.leads import Lead, LeadCreate
from app.services import leads
from fastapi import HTTPException
from pydantic import ValidationError


def _lead_row(**kw):
    base = {
        "id": uuid.uuid4(),
        "business_name": "Acme",
        "contact_name": "Priya",
        "contact_email": "priya@acme.com",
        "contact_phone": "+919876543210",
        "message": "interested",
        "source": "hero",
        "status": "new",
        "created_at": datetime.now(UTC),
    }
    base.update(kw)
    return base


# --- model validation --------------------------------------------------------


def test_lead_create_rejects_bad_email():
    with pytest.raises(ValidationError):
        LeadCreate(contact_email="not-an-email")


def test_lead_create_valid():
    body = LeadCreate(contact_email="a@b.com", business_name="X")
    assert body.contact_email == "a@b.com"
    assert body.contact_name is None


# --- create / list / update --------------------------------------------------


async def test_create_lead(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(leads, "get_pool", lambda: pool)
    conn.fetchrow.return_value = _lead_row()

    lead = await leads.create_lead(
        LeadCreate(contact_email="priya@acme.com", business_name="Acme", source="hero")
    )

    assert isinstance(lead, Lead)
    assert lead.contact_email == "priya@acme.com"
    assert lead.status == "new"


async def test_list_leads_with_status(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(leads, "get_pool", lambda: pool)
    conn.fetch.return_value = [_lead_row(status="contacted")]

    result = await leads.list_leads(status="contacted")

    assert result[0].status == "contacted"
    assert conn.fetch.await_args.args[1] == "contacted"  # status param bound


async def test_update_lead_status_success(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(leads, "get_pool", lambda: pool)
    lead_id = uuid.uuid4()
    conn.fetchrow.return_value = _lead_row(id=lead_id, status="converted")

    lead = await leads.update_lead_status(lead_id, "converted")

    assert lead.status == "converted"


async def test_update_lead_status_404(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    monkeypatch.setattr(leads, "get_pool", lambda: pool)
    conn.fetchrow.return_value = None

    with pytest.raises(HTTPException) as exc:
        await leads.update_lead_status(uuid.uuid4(), "lost")
    assert exc.value.status_code == 404


# --- notify ------------------------------------------------------------------


async def test_notify_skips_without_inbox(monkeypatch):
    monkeypatch.setattr(
        leads, "get_settings", lambda: SimpleNamespace(leads_notify_email="")
    )
    send = AsyncMock()
    monkeypatch.setattr(leads, "send_email", send)

    await leads.notify_team_of_lead(Lead.model_validate(_lead_row()))

    send.assert_not_awaited()


async def test_notify_sends_with_inbox(monkeypatch):
    monkeypatch.setattr(
        leads,
        "get_settings",
        lambda: SimpleNamespace(leads_notify_email="ops@zerqo.in"),
    )
    send = AsyncMock(return_value=True)
    monkeypatch.setattr(leads, "send_email", send)

    await leads.notify_team_of_lead(Lead.model_validate(_lead_row()))

    send.assert_awaited_once()
    assert send.await_args.kwargs["to"] == "ops@zerqo.in"
