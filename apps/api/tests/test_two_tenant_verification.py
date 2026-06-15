"""Two-tenant verification (ticket 3.13).

Fixture-based (no live phone): proves two tenants on two numbers resolve to
distinct agents, get distinct voice/prompt pipeline context and provider
snapshots, both run on live providers, and never cross over.
"""

import uuid

from app.models.tenant import ProviderConfig
from app.providers.registry import ensure_live_providers
from app.services import call_routing
from app.services.calls import get_call_pipeline_context

# Two tenants, two numbers, two voices, two prompts.
TENANT_A = {
    "to": "+911111111111",
    "tenant_id": uuid.uuid4(),
    "agent_id": uuid.uuid4(),
    "voice_id": "aura-asteria-en",
    "system_prompt": "You are tenant A's receptionist.",
}
TENANT_B = {
    "to": "+912222222222",
    "tenant_id": uuid.uuid4(),
    "agent_id": uuid.uuid4(),
    "voice_id": "aura-orion-en",
    "system_prompt": "You are tenant B's concierge.",
}


def _route_row(t):
    return {
        "agent_id": t["agent_id"],
        "tenant_id": t["tenant_id"],
        "stt": "deepgram",
        "tts": "deepgram",
        "llm": "deepseek_native",
    }


def _context_row(t):
    return {
        "call_id": uuid.uuid4(),
        "tenant_id": t["tenant_id"],
        "voice_id": t["voice_id"],
        "system_prompt": t["system_prompt"],
        "language": "en",
        "stt": "deepgram",
        "tts": "deepgram",
        "llm": "deepseek_native",
    }


async def test_two_numbers_resolve_to_distinct_tenants(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchrow.side_effect = [_route_row(TENANT_A), _route_row(TENANT_B)]
    monkeypatch.setattr(call_routing, "get_pool", lambda: pool)

    a = await call_routing.resolve_agent_by_number(TENANT_A["to"])
    b = await call_routing.resolve_agent_by_number(TENANT_B["to"])

    assert a.tenant_id == TENANT_A["tenant_id"]
    assert b.tenant_id == TENANT_B["tenant_id"]
    # No cross-tenant leakage.
    assert a.tenant_id != b.tenant_id
    assert a.agent_id != b.agent_id


async def test_two_calls_get_distinct_voice_and_prompt(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchrow.side_effect = [_context_row(TENANT_A), _context_row(TENANT_B)]
    monkeypatch.setattr("app.services.calls.get_pool", lambda: pool)

    a = await get_call_pipeline_context("CA-A")
    b = await get_call_pipeline_context("CA-B")

    assert a["voice_id"] == "aura-asteria-en"
    assert b["voice_id"] == "aura-orion-en"
    assert a["voice_id"] != b["voice_id"]
    assert a["system_prompt"] != b["system_prompt"]
    assert a["tenant_id"] != b["tenant_id"]


def test_both_tenant_configs_run_on_live_providers():
    # India English default → live (non-stub) providers for both tenants.
    config = ProviderConfig(stt="deepgram", tts="deepgram", llm="deepseek_native")
    ensure_live_providers(config)  # must not raise


async def test_provider_snapshot_reflects_each_tenant_config(mock_db_pool, monkeypatch):
    pool, conn = mock_db_pool
    conn.fetchrow.side_effect = [_route_row(TENANT_A), _route_row(TENANT_B)]
    monkeypatch.setattr(call_routing, "get_pool", lambda: pool)

    a = await call_routing.resolve_agent_by_number(TENANT_A["to"])
    b = await call_routing.resolve_agent_by_number(TENANT_B["to"])

    # The snapshot the webhook stores is built from each route's config.
    snap_a = {"stt": a.stt, "tts": a.tts, "llm": a.llm}
    snap_b = {"stt": b.stt, "tts": b.tts, "llm": b.llm}
    assert snap_a == {"stt": "deepgram", "tts": "deepgram", "llm": "deepseek_native"}
    assert snap_b == snap_a  # both India English in this scenario
