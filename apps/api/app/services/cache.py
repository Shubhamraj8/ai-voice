"""Upstash Redis (REST) cache helper (ticket 4.05).

A best-effort cache over Upstash's HTTP API. It is fully optional: when
``UPSTASH_REDIS_URL`` / ``UPSTASH_REDIS_TOKEN`` are unset, or the request fails,
every operation degrades to a no-op (get → None, set → silently skipped) so the
caller simply does the underlying work uncached. Never raises to the caller.

Used for query-embedding caching now (5-minute TTL) and tool rate limits later
(4.12).
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


def _is_configured() -> bool:
    settings = get_settings()
    return bool(settings.upstash_redis_url and settings.upstash_redis_token)


async def _command(*args: Any) -> Any | None:
    """Run a single Redis command via the Upstash REST API.

    Returns the ``result`` field, or None when caching is disabled or the call
    fails (logged at warning level, never raised).
    """

    if not _is_configured():
        return None

    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                settings.upstash_redis_url.rstrip("/"),
                json=[str(a) for a in args],
                headers={"Authorization": f"Bearer {settings.upstash_redis_token}"},
            )
            resp.raise_for_status()
            return resp.json().get("result")
    except Exception as exc:
        logger.warning("redis_command_failed", command=args[0], error=str(exc))
        return None


async def get_json(key: str) -> Any | None:
    """Return the JSON value stored at ``key``, or None on miss / disabled."""

    raw = await _command("GET", key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


async def set_json(key: str, value: Any, *, ttl_s: int) -> None:
    """Store ``value`` (JSON-encoded) at ``key`` with an expiry. Best-effort."""

    await _command("SET", key, json.dumps(value), "EX", ttl_s)


async def incr_with_ttl(key: str, *, ttl_s: int) -> int | None:
    """Increment ``key`` and (re)set its expiry; return the new count, or None
    when caching is disabled/unavailable (so callers can skip enforcement)."""

    value = await _command("INCR", key)
    if value is None:
        return None
    await _command("EXPIRE", key, ttl_s)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
