"""Pydantic schemas for encrypted emotion inference and analysis."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EncryptedImageRequest(BaseModel):
    ciphertext: str = Field(..., description="Serialized encrypted image payload")
    key_id: str = Field(..., description="Logical identifier of the client key")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional client-side metadata")
    date: Optional[date] = Field(default=None, description="Optional target date (YYYY-MM-DD)")


class EncryptedPredictionResponse(BaseModel):
    ciphertext: str
    date: date


class NDayAnalysisRequest(BaseModel):
    days: Optional[int] = None


class EncryptedNDayAnalysisResponse(BaseModel):
    ciphertext: str


# HE key registration and history (raw encrypted) --------------------------------
class HEKeyRegisterRequest(BaseModel):
    key_id: str
    eval_context_b64: str


class EncryptedDailyPrediction(BaseModel):
    date: date
    ciphertext: str


class EncryptedHistoryResponse(BaseModel):
    key_id: str
    days: int
    entries: List[EncryptedDailyPrediction]

class EncryptedStatsRequest(BaseModel):
    days: int
    key_id: str

class EncryptedStatsResponse(BaseModel):
    encrypted_sum: str
    encrypted_volatility: str
