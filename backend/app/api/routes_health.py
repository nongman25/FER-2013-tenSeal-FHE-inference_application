"""Health check endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import HealthStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(status="ok")
