import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_SUPABASE_TESTS") != "1",
    reason="Set RUN_LIVE_SUPABASE_TESTS=1 to run live Supabase integration tests",
)


def test_service_role_client_reads_tenants():
    from app.db.supabase import get_service_role_client

    client = get_service_role_client()
    result = client.table("tenants").select("id").limit(1).execute()
    assert result.data is not None
