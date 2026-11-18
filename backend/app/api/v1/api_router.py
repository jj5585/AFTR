from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.invitations import router as invitations_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.posts import router as posts_router
from backend.app.api.v1.moderation import router as moderation_router
from backend.app.api.v1.discovery import discovery_router, connections_router
from backend.app.api.v1.messaging import router as messaging_router
from backend.app.api.v1.stories import router as stories_router
from backend.app.api.v1.events import router as events_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(invitations_router)
api_router.include_router(auth_router)
api_router.include_router(posts_router)
api_router.include_router(moderation_router)
api_router.include_router(discovery_router)
api_router.include_router(connections_router)
api_router.include_router(messaging_router)
api_router.include_router(stories_router)
api_router.include_router(events_router)
