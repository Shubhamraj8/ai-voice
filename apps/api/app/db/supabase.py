from supabase import Client, create_client

from app.config import get_settings


def get_service_role_client() -> Client:
    """
    Returns a Supabase client instantiated with the Service Role key.

    WARNING: This client bypasses Row Level Security (RLS) entirely.
    It should ONLY be used for backend administrative actions (e.g., Auth Admin API)
    or internal jobs where RLS bypass is explicitly intended.

    For all other database interactions on behalf of a user, use the `asyncpg` pool
    with appropriate tenant contexts, which will enforce RLS.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
