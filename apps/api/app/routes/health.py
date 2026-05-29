from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.db.pool import ping_pool

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "hello-world"}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description=(
        "Returns API status, current UTC timestamp, " "and database connection status."
    ),
)
async def health(request: Request) -> HealthResponse:
    pool = request.app.state.db_pool
    db_status = await ping_pool(pool)
    logger.info("health_check", **db_status)
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(UTC),
        database=db_status.get("database", "unknown"),
    )
