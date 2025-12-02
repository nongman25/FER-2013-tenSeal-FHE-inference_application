"""Emotion inference and history routes."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.emotion import (
    EncryptedImageRequest,
    EncryptedNDayAnalysisResponse,
    EncryptedPredictionResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.emotion_service import EmotionService

router = APIRouter(prefix="/emotion", tags=["emotion"])


def get_emotion_service(request: Request) -> EmotionService:
    return request.app.state.emotion_service


def get_analysis_service(request: Request) -> AnalysisService:
    return request.app.state.analysis_service


@router.post("/analyze-today", response_model=EncryptedPredictionResponse)
def analyze_today(
    payload: EncryptedImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    emotion_service: EmotionService = Depends(get_emotion_service),
) -> EncryptedPredictionResponse:
    tz = ZoneInfo(settings.EMOTION_DB_TIMEZONE)
    today = datetime.now(tz=tz).date()
    return emotion_service.analyze_and_store(
        db=db,
        user_id=current_user.user_id,
        target_date=today,
        enc_image_payload=payload.ciphertext,
        key_id=payload.key_id,
    )


@router.get("/history", response_model=EncryptedNDayAnalysisResponse)
def history(
    days: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> EncryptedNDayAnalysisResponse:
    window = days or settings.EMOTION_ANALYSIS_DAYS
    ciphertext = analysis_service.analyze_recent_days(db, current_user.user_id, window)
    return EncryptedNDayAnalysisResponse(ciphertext=ciphertext)
