from dataclasses import dataclass
from typing import Self
from urllib.parse import quote

import httpx

from app.config import get_settings


@dataclass
class QueryResult:
    data: list[dict]
    count: int | None = None


class TableQuery:
    def __init__(self, base_url: str, service_role_key: str, table: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_role_key = service_role_key
        self._table = table
        self._columns = "*"
        self._count: str | None = None
        self._limit: int | None = None

    def select(self, *columns: str, count: str | None = None) -> Self:
        self._columns = ",".join(columns) if columns else "*"
        self._count = count
        return self

    def limit(self, n: int) -> Self:
        self._limit = n
        return self

    def execute(self) -> QueryResult:
        params: dict[str, str] = {"select": self._columns}
        if self._limit is not None:
            params["limit"] = str(self._limit)

        headers = {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
        }
        if self._count == "exact":
            headers["Prefer"] = "count=exact"

        response = httpx.get(
            f"{self._base_url}/rest/v1/{quote(self._table, safe='')}",
            params=params,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()

        total_count: int | None = None
        if self._count == "exact":
            content_range = response.headers.get("Content-Range", "")
            if "/" in content_range:
                total_count = int(content_range.rsplit("/", maxsplit=1)[-1])

        return QueryResult(data=response.json(), count=total_count)


class ServiceRoleClient:
    """Minimal PostgREST client using the Supabase service role key (RLS bypass)."""

    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self._supabase_url = supabase_url
        self._service_role_key = service_role_key

    def table(self, name: str) -> TableQuery:
        return TableQuery(self._supabase_url, self._service_role_key, name)


def get_service_role_client() -> ServiceRoleClient:
    """
    Returns a Supabase PostgREST client with the service role key.

    WARNING: This client bypasses Row Level Security (RLS) entirely.
    Use only for trusted backend administrative / internal operations.
    """
    settings = get_settings()
    return ServiceRoleClient(settings.supabase_url, settings.supabase_service_role_key)
