"""SQLAlchemy model for encrypted emotion predictions."""
from __future__ import annotations

from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT

from app.core.db import Base


class EmotionData(Base):
    __tablename__ = "emotiondata"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_emotiondata_user_date"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("user.user_id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    enc_prediction = Column(LONGTEXT, nullable=False)
