"""
Cross-tenant RLS smoke test (ticket 1.05).

Requires .env with SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.
Run: pnpm test:rls
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

pytestmark = pytest.mark.skipif(
    not (SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY),
    reason="Supabase env vars required for RLS integration test",
)

TENANT_SCOPED_TABLES = ("agents", "calls", "call_messages", "audit_log")


def _require_env() -> None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_ROLE_KEY:
        pytest.skip("Missing Supabase environment variables")


class SupabaseClient:
    def __init__(self, key: str, access_token: str | None = None) -> None:
        self._key = key
        self._token = access_token or key

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def auth_sign_in(self, email: str, password: str) -> str:
        response = httpx.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": self._key, "Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=30.0,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        assert token
        self._token = token
        return token

    def auth_admin_create_user(self, email: str, password: str) -> dict[str, Any]:
        response = httpx.post(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers=self._headers(),
            json={"email": email, "password": password, "email_confirm": True},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def auth_admin_delete_user(self, user_id: str) -> None:
        response = httpx.delete(
            f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers=self._headers(),
            timeout=30.0,
        )
        response.raise_for_status()

    def insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        response = httpx.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=self._headers(prefer="return=representation"),
            json=row,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: dict[str, str] | None = None,
        in_filters: dict[str, list[str]] | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"select": columns}
        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"
        if in_filters:
            for key, values in in_filters.items():
                params[key] = f"in.({','.join(values)})"
        response = httpx.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=self._headers(),
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def update(self, table: str, row: dict[str, Any], filters: dict[str, str]) -> list[dict[str, Any]]:
        params = {key: f"eq.{value}" for key, value in filters.items()}
        response = httpx.patch(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=self._headers(prefer="return=representation"),
            params=params,
            json=row,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def delete(self, table: str, filters: dict[str, str]) -> list[dict[str, Any]]:
        params = {key: f"eq.{value}" for key, value in filters.items()}
        response = httpx.delete(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=self._headers(prefer="return=representation"),
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    def delete_in(self, table: str, column: str, values: list[str]) -> None:
        params = {column: f"in.({','.join(values)})"}
        response = httpx.delete(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=self._headers(),
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()


@pytest.fixture(scope="module")
def admin_client() -> SupabaseClient:
    _require_env()
    return SupabaseClient(SUPABASE_SERVICE_ROLE_KEY)


@pytest.fixture(scope="module")
def seed_data(admin_client: SupabaseClient) -> dict[str, Any]:
    suffix = uuid.uuid4().hex[:8]
    password = f"Test-Rls-{suffix}!Aa1"

    user_a = admin_client.auth_admin_create_user(
        f"rls-a-{suffix}@example.com", password
    )
    user_b = admin_client.auth_admin_create_user(
        f"rls-b-{suffix}@example.com", password
    )
    user_internal = admin_client.auth_admin_create_user(
        f"rls-internal-{suffix}@example.com", password
    )

    tenant_a = admin_client.insert(
        "tenants",
        {"slug": f"tenant-a-{suffix}", "business_name": f"Tenant A {suffix}"},
    )[0]
    tenant_b = admin_client.insert(
        "tenants",
        {"slug": f"tenant-b-{suffix}", "business_name": f"Tenant B {suffix}"},
    )[0]

    admin_client.insert(
        "tenant_users",
        {"tenant_id": tenant_a["id"], "user_id": user_a["id"], "role": "owner"},
    )
    admin_client.insert(
        "tenant_users",
        {"tenant_id": tenant_b["id"], "user_id": user_b["id"], "role": "owner"},
    )
    admin_client.insert(
        "internal_users",
        {"user_id": user_internal["id"], "role": "admin"},
    )

    agent_a = admin_client.insert(
        "agents",
        {
            "tenant_id": tenant_a["id"],
            "name": "Agent A",
            "starter_prompt": "generic_support",
            "system_prompt": "You are agent A",
            "voice_id": "voice-a",
            "phone_number": f"+9100000{suffix[:4]}01",
            "twilio_sid": f"TW-A-{suffix}",
        },
    )[0]
    agent_b = admin_client.insert(
        "agents",
        {
            "tenant_id": tenant_b["id"],
            "name": "Agent B",
            "starter_prompt": "generic_support",
            "system_prompt": "You are agent B",
            "voice_id": "voice-b",
            "phone_number": f"+9100000{suffix[:4]}02",
            "twilio_sid": f"TW-B-{suffix}",
        },
    )[0]

    call_a = admin_client.insert(
        "calls",
        {
            "tenant_id": tenant_a["id"],
            "agent_id": agent_a["id"],
            "twilio_call_sid": f"CA-A-{suffix}",
            "from_number": "+911111111111",
        },
    )[0]
    call_b = admin_client.insert(
        "calls",
        {
            "tenant_id": tenant_b["id"],
            "agent_id": agent_b["id"],
            "twilio_call_sid": f"CA-B-{suffix}",
            "from_number": "+912222222222",
        },
    )[0]

    admin_client.insert(
        "call_messages",
        {
            "call_id": call_a["id"],
            "tenant_id": tenant_a["id"],
            "role": "user",
            "content": "hello from A",
        },
    )
    admin_client.insert(
        "call_messages",
        {
            "call_id": call_b["id"],
            "tenant_id": tenant_b["id"],
            "role": "user",
            "content": "hello from B",
        },
    )

    admin_client.insert(
        "audit_log",
        {
            "actor_user_id": user_a["id"],
            "actor_type": "tenant_user",
            "tenant_id": tenant_a["id"],
            "action": "test.seed",
            "payload": {"tenant": "a"},
        },
    )
    admin_client.insert(
        "audit_log",
        {
            "actor_user_id": user_b["id"],
            "actor_type": "tenant_user",
            "tenant_id": tenant_b["id"],
            "action": "test.seed",
            "payload": {"tenant": "b"},
        },
    )

    data = {
        "suffix": suffix,
        "password": password,
        "user_a_id": user_a["id"],
        "user_b_id": user_b["id"],
        "user_internal_id": user_internal["id"],
        "user_a_email": f"rls-a-{suffix}@example.com",
        "user_b_email": f"rls-b-{suffix}@example.com",
        "user_internal_email": f"rls-internal-{suffix}@example.com",
        "tenant_a_id": tenant_a["id"],
        "tenant_b_id": tenant_b["id"],
        "agent_a_id": agent_a["id"],
        "agent_b_id": agent_b["id"],
        "call_a_id": call_a["id"],
        "call_b_id": call_b["id"],
    }

    yield data

    admin_client.delete_in("audit_log", "tenant_id", [tenant_a["id"], tenant_b["id"]])
    admin_client.delete_in("call_messages", "tenant_id", [tenant_a["id"], tenant_b["id"]])
    admin_client.delete_in("calls", "id", [call_a["id"], call_b["id"]])
    admin_client.delete_in("agents", "id", [agent_a["id"], agent_b["id"]])
    admin_client.delete_in("tenant_users", "tenant_id", [tenant_a["id"], tenant_b["id"]])
    admin_client.delete("internal_users", {"user_id": user_internal["id"]})
    admin_client.delete_in("tenants", "id", [tenant_a["id"], tenant_b["id"]])
    admin_client.auth_admin_delete_user(user_a["id"])
    admin_client.auth_admin_delete_user(user_b["id"])
    admin_client.auth_admin_delete_user(user_internal["id"])


def user_client(email: str, password: str) -> SupabaseClient:
    client = SupabaseClient(SUPABASE_ANON_KEY)
    client.auth_sign_in(email, password)
    return client


def test_rls_select_isolation(seed_data: dict[str, Any]) -> None:
    client = user_client(seed_data["user_a_email"], seed_data["password"])

    tenants = client.select("tenants", columns="id")
    tenant_ids = {row["id"] for row in tenants}
    assert tenant_ids == {seed_data["tenant_a_id"]}

    for table in TENANT_SCOPED_TABLES:
        rows = client.select(table, columns="tenant_id")
        assert rows, f"expected rows in {table} for tenant A"
        assert all(row["tenant_id"] == seed_data["tenant_a_id"] for row in rows)

    agent_b = client.select("agents", columns="id", filters={"id": seed_data["agent_b_id"]})
    assert agent_b == []


def test_rls_insert_update_delete_blocked(seed_data: dict[str, Any]) -> None:
    client = user_client(seed_data["user_a_email"], seed_data["password"])

    response = httpx.post(
        f"{SUPABASE_URL}/rest/v1/agents",
        headers=client._headers(prefer="return=representation"),
        json={
            "tenant_id": seed_data["tenant_b_id"],
            "name": "Intruder Agent",
            "starter_prompt": "generic_support",
            "system_prompt": "blocked",
            "voice_id": "x",
            "phone_number": f"+9199999{seed_data['suffix']}",
            "twilio_sid": f"TW-X-{seed_data['suffix']}",
        },
        timeout=30.0,
    )
    assert response.status_code in (401, 403) or response.json() == []

    updated = client.update("agents", {"name": "Hacked"}, {"id": seed_data["agent_b_id"]})
    assert updated == []

    deleted = client.delete("calls", {"id": seed_data["call_b_id"]})
    assert deleted == []


def test_internal_user_full_access(seed_data: dict[str, Any]) -> None:
    client = user_client(seed_data["user_internal_email"], seed_data["password"])

    tenants = client.select("tenants", columns="id")
    tenant_ids = {row["id"] for row in tenants}
    assert seed_data["tenant_a_id"] in tenant_ids
    assert seed_data["tenant_b_id"] in tenant_ids

    agents = client.select(
        "agents",
        columns="id",
        in_filters={"id": [seed_data["agent_a_id"], seed_data["agent_b_id"]]},
    )
    assert len(agents) == 2
