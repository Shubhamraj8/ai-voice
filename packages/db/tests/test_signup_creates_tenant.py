"""
Signup tenant provisioning smoke test (ticket 1.09).

Requires .env with SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY.
Run: pnpm --filter @ai-voice/db run test:signup-tenant
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
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

pytestmark = pytest.mark.skipif(
    not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY),
    reason="Supabase env vars required for signup tenant test",
)

INDIA_PROVIDER_CONFIG = {"stt": "cartesia", "tts": "inworld", "llm": "deepseek_native"}


def admin_headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def fetch_tenant_membership(user_id: str) -> list[dict[str, Any]]:
    response = httpx.get(
        f"{SUPABASE_URL}/rest/v1/tenant_users",
        headers=admin_headers(),
        params={
            "user_id": f"eq.{user_id}",
            "select": "role,tenant_id,tenants(id,slug,market,language,provider_config)",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def test_signup_creates_one_tenant_and_owner() -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f"signup-tenant-{suffix}@example.com"
    password = f"Test-Signup-{suffix}!Aa1"
    user_id: str | None = None
    tenant_id: str | None = None

    try:
        create_resp = httpx.post(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers=admin_headers(),
            json={"email": email, "password": password, "email_confirm": True},
            timeout=30.0,
        )
        create_resp.raise_for_status()
        user_id = create_resp.json()["id"]

        rows = fetch_tenant_membership(user_id)
        assert len(rows) == 1, "expected exactly one tenant for new user"

        row = rows[0]
        tenant_id = row["tenant_id"]
        assert row["role"] == "owner"

        tenant = row["tenants"]
        assert tenant["market"] == "india_english"
        assert tenant["language"] == "en"
        assert tenant["provider_config"] == INDIA_PROVIDER_CONFIG

        # Idempotent membership count (trigger guard).
        assert len(fetch_tenant_membership(user_id)) == 1

    finally:
        if tenant_id:
            httpx.delete(
                f"{SUPABASE_URL}/rest/v1/tenants",
                headers=admin_headers(),
                params={"id": f"eq.{tenant_id}"},
                timeout=30.0,
            )
        if user_id:
            httpx.delete(
                f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                headers=admin_headers(),
                timeout=30.0,
            )
