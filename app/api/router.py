from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.settings import router as settings_router
from app.api.trends import router as trends_router
from app.api.md import router as md_router

router = APIRouter()
router.include_router(health_router)
router.include_router(settings_router)
router.include_router(trends_router)
router.include_router(md_router)