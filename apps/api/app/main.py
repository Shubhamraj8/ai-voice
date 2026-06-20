import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.pool import close_pool, create_pool
from app.logging_config import configure_logging
from app.middleware.request_id import RequestIdMiddleware
from app.routes import api_router
from app.services.agent_sweeper import run_agent_sweeper
from app.services.calls_reaper import run_stale_call_reaper
from app.services.recording_retention import run_recording_retention
from app.services.subscription_expiry import run_subscription_expiry
from app.services.usage_aggregation import run_usage_aggregation

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("app_starting", cors_origins=settings.cors_origin_list)
    app.state.db_pool = await create_pool(settings.database_url)
    reaper_task = asyncio.create_task(run_stale_call_reaper())
    sweeper_task = asyncio.create_task(run_agent_sweeper())
    expiry_task = asyncio.create_task(run_subscription_expiry())
    usage_task = asyncio.create_task(run_usage_aggregation())
    retention_task = asyncio.create_task(run_recording_retention())
    try:
        yield
    finally:
        reaper_task.cancel()
        sweeper_task.cancel()
        expiry_task.cancel()
        usage_task.cancel()
        retention_task.cancel()
        with suppress(asyncio.CancelledError):
            await reaper_task
        with suppress(asyncio.CancelledError):
            await sweeper_task
        with suppress(asyncio.CancelledError):
            await expiry_task
        with suppress(asyncio.CancelledError):
            await usage_task
        with suppress(asyncio.CancelledError):
            await retention_task
        await close_pool(app.state.db_pool)
        logger.info("app_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="AI Voice API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)
    return application


app = create_app()
