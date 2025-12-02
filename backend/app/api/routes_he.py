"""HE key registration endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.emotion import HEKeyRegisterRequest
from app.services.he_service import HEEmotionEngine

router = APIRouter(prefix="/he", tags=["he"])


def get_he_engine(request: Request) -> HEEmotionEngine:
    return request.app.state.he_engine


@router.post("/register-key")
def register_key(
    payload: HEKeyRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # noqa: ARG001 - ensures auth
    he_engine: HEEmotionEngine = Depends(get_he_engine),
) -> dict[str, str]:
    he_engine.register_eval_context(key_id=payload.key_id, eval_context_b64=payload.eval_context_b64)
    return {"status": "ok", "key_id": payload.key_id}
