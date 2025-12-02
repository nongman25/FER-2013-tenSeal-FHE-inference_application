"""Domain service orchestrating encrypted single-day emotion analysis."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.repositories.emotion_data_repository import EmotionDataRepository
from app.schemas.emotion import EncryptedPredictionResponse
from app.services.he_service import HEEmotionEngine


class EmotionService:
    def __init__(self, repo: EmotionDataRepository, he_engine: HEEmotionEngine) -> None:
        self.repo = repo
        self.he_engine = he_engine

    def analyze_and_store(
        self,
        db: Session,
        user_id: str,
        target_date: date,
        enc_image_payload: str,
        key_id: str,
    ) -> EncryptedPredictionResponse:
        # Log entry
        enc_prediction = self.he_engine.run_encrypted_inference(enc_image_payload, key_id)
        # Store encrypted logits (or summary if postprocess changes in future)
        self.repo.upsert_enc_prediction(db, user_id, target_date, enc_prediction)
        return EncryptedPredictionResponse(ciphertext=enc_prediction, date=target_date)

    def get_raw_history(self, db: Session, user_id: str, days: int):
        return self.repo.get_recent_enc_predictions(db, user_id, days)
