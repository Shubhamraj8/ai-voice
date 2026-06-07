import asyncio
from typing import Any

import asyncpg
import structlog

logger = structlog.get_logger(__name__)

_pool: asyncpg.Pool | None = None

DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY_SEC = 0.5


async def create_pool(
    database_url: str,
    *,
    min_size: int = 1,
    max_size: int = 10,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> asyncpg.Pool:
    """Create asyncpg pool with exponential backoff on transient connection errors."""
    global _pool
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            pool = await asyncpg.create_pool(
                database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
                statement_cache_size=0,
            )
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            _pool = pool
            logger.info(
                "database_pool_ready",
                min_size=min_size,
                max_size=max_size,
                attempt=attempt,
            )
            return pool
        except (OSError, asyncpg.PostgresError, TimeoutError) as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            delay = DEFAULT_BASE_DELAY_SEC * (2 ** (attempt - 1))
            logger.warning(
                "database_pool_retry",
                attempt=attempt,
                max_retries=max_retries,
                delay_sec=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)

    assert last_error is not None
    logger.error("database_pool_failed", error=str(last_error))
    raise last_error


async def close_pool(pool: asyncpg.Pool | None = None) -> None:
    global _pool
    target = pool or _pool
    if target is not None:
        await target.close()
        logger.info("database_pool_closed")
    _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool


async def ping_pool(pool: asyncpg.Pool) -> dict[str, Any]:
    async with pool.acquire() as conn:
        value = await conn.fetchval("SELECT 1")
    return {"database": "ok" if value == 1 else "unexpected"}
