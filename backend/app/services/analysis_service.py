"""Service skeleton for N-day encrypted analysis."""
from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session

from app.repositories.emotion_data_repository import EmotionDataRepository
from app.services.he_service import HEEmotionEngine


class AnalysisService:
    def __init__(self, repo: EmotionDataRepository, he_engine: HEEmotionEngine) -> None:
        self.repo = repo
        self.he_engine = he_engine

    def analyze_recent_days(self, db: Session, user_id: str, days: int) -> str:
        records = self.repo.get_recent_enc_predictions(db, user_id, days)
        enc_summaries = [record.enc_prediction for record in records]
        if enc_summaries:
            # TODO: implement real HE aggregation (frequency, run-length, transitions)
            return enc_summaries[0]
        # No data yet; return a stub summary ciphertext for the client to decrypt
        return self.he_engine.postprocess_prediction_to_summary("", date.today())
