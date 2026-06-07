"""Twilio Media Streams WebSocket handler (ticket 2.04)."""

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.services.voice.pipeline import run_minimal_twilio_pipeline

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/twilio", tags=["twilio-media"])


@router.websocket(
    "/media",
    name="twilio_media_stream",
)
async def twilio_media_stream(websocket: WebSocket) -> None:
    """Accept Twilio Media Streams and run the Pipecat voice pipeline."""
    await websocket.accept()
    settings = get_settings()

    logger.info("twilio_media_websocket_accepted")

    try:
        await run_minimal_twilio_pipeline(websocket, settings)
    except WebSocketDisconnect:
        logger.info("twilio_media_websocket_disconnect")
    except Exception as exc:
        logger.exception(
            "twilio_media_websocket_error",
            error=str(exc),
        )
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
    finally:
        logger.info("twilio_media_websocket_closed")
