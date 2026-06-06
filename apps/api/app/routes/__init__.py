from fastapi import APIRouter

from app.routes import health, internal, me, twilio_webhooks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(internal.router)
api_router.include_router(twilio_webhooks.router)
