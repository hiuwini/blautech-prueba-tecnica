from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    return {"status": "ok", "service": request.app.state.config.service_name}
