from fastapi import APIRouter

from app.routes import (
    health,
    internal,
    internal_agents,
    internal_knowledge,
    internal_leads,
    internal_tenants,
    leads,
    me,
    pricing,
    twilio_media,
    twilio_webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(pricing.router)
api_router.include_router(leads.router)
api_router.include_router(internal.router)
api_router.include_router(internal_tenants.router)
api_router.include_router(internal_agents.router)
api_router.include_router(internal_knowledge.router)
api_router.include_router(internal_leads.router)
api_router.include_router(twilio_webhooks.router)
api_router.include_router(twilio_media.router)
