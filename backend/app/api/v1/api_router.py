from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.invitations import router as invitations_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.posts import router as posts_router
from backend.app.api.v1.moderation import router as moderation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(invitations_router)
api_router.include_router(auth_router)
api_router.include_router(posts_router)
api_router.include_router(moderation_router)
