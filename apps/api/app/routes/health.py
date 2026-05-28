import structlog
from fastapi import APIRouter, Request

from app.db.pool import ping_pool

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "hello-world"}


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    pool = request.app.state.db_pool
    db_status = await ping_pool(pool)
    logger.info("health_check", **db_status)
    return {"status": "ok", **db_status}
