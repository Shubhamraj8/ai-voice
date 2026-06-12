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
from app.services.calls_reaper import run_stale_call_reaper

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("app_starting", cors_origins=settings.cors_origin_list)
    app.state.db_pool = await create_pool(settings.database_url)
    reaper_task = asyncio.create_task(run_stale_call_reaper())
    try:
        yield
    finally:
        reaper_task.cancel()
        with suppress(asyncio.CancelledError):
            await reaper_task
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
