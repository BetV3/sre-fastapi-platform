"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.items import router as items_router

router = APIRouter()

router.include_router(health_router, tags=["Health"])
router.include_router(items_router, prefix="/items", tags=["Items"])
