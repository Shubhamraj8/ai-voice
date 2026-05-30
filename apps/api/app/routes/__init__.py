from fastapi import APIRouter

from app.routes import health, internal, me

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(internal.router)
