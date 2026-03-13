from fastapi import APIRouter

from .chat_routes import router as chat_router
from .index_routes import router as index_router
from .document_routes import router as document_router
from .health_routes import router as health_router

router = APIRouter()

router.include_router(chat_router)
router.include_router(index_router)
router.include_router(document_router)
router.include_router(health_router)
