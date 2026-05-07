from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.documents.routes import router as documents_router


router = APIRouter(prefix="/api/v1")
router.include_router(documents_router)
