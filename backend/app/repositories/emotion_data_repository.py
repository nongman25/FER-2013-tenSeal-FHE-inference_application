"""Repository for encrypted emotion prediction storage."""
from __future__ import annotations

from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.emotion_data import EmotionData
import logging

LOGGER = logging.getLogger(__name__)


class EmotionDataRepository:
    def upsert_enc_prediction(self, db: Session, user_id: str, date_value: date, enc_prediction: str) -> EmotionData:
        try:
            record = (
                db.query(EmotionData)
                .filter(EmotionData.user_id == user_id, EmotionData.date == date_value)
                .one_or_none()
            )
            if record:
                record.enc_prediction = enc_prediction
            else:
                record = EmotionData(user_id=user_id, date=date_value, enc_prediction=enc_prediction)
                db.add(record)
            db.commit()
            db.refresh(record)
            return record
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            LOGGER.error("DB upsert failed for user=%s date=%s (len=%s): %s", user_id, date_value, len(enc_prediction), exc)
            raise

    def get_recent_enc_predictions(self, db: Session, user_id: str, days: int) -> list[EmotionData]:
        start_date = date.today() - timedelta(days=max(days - 1, 0))
        return (
            db.query(EmotionData)
            .filter(EmotionData.user_id == user_id, EmotionData.date >= start_date)
            .order_by(EmotionData.date.desc())
            .all()
        )
