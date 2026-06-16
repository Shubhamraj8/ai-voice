"""Tests for the Upstash Redis cache helper (ticket 4.05). No network calls."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.services import cache


def _disabled_settings():
    return SimpleNamespace(upstash_redis_url="", upstash_redis_token="")


def _enabled_settings():
    return SimpleNamespace(
        upstash_redis_url="https://example.upstash.io",
        upstash_redis_token="tok",
    )


# --- disabled (no creds) → graceful no-op ------------------------------------


async def test_get_json_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr(cache, "get_settings", _disabled_settings)
    assert await cache.get_json("k") is None


async def test_set_json_is_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(cache, "get_settings", _disabled_settings)
    # Must not raise even though nothing is stored.
    assert await cache.set_json("k", [1.0, 2.0], ttl_s=300) is None


# --- get_json parsing --------------------------------------------------------


async def test_get_json_parses_result(monkeypatch):
    monkeypatch.setattr(cache, "_command", AsyncMock(return_value="[0.1, 0.2]"))
    assert await cache.get_json("k") == [0.1, 0.2]


async def test_get_json_miss_returns_none(monkeypatch):
    monkeypatch.setattr(cache, "_command", AsyncMock(return_value=None))
    assert await cache.get_json("k") is None


async def test_get_json_bad_payload_returns_none(monkeypatch):
    monkeypatch.setattr(cache, "_command", AsyncMock(return_value="not-json"))
    assert await cache.get_json("k") is None


# --- set_json wiring ---------------------------------------------------------


async def test_set_json_issues_set_with_expiry(monkeypatch):
    command = AsyncMock(return_value="OK")
    monkeypatch.setattr(cache, "_command", command)

    await cache.set_json("emb:k", [0.5], ttl_s=300)

    command.assert_awaited_once_with("SET", "emb:k", "[0.5]", "EX", 300)
