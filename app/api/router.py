from fastapi import APIRouter

from .health import router as health_router
from .trends import router as trends_router
from .settings import router as settings_router
from .md import router as md_router
from .chat import router as chat_router
from .archive import router as archive_router  

router = APIRouter(prefix="/api")

router.include_router(health_router)
router.include_router(trends_router)
router.include_router(settings_router)
router.include_router(md_router)
router.include_router(chat_router)
router.include_router(archive_router)  