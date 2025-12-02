"""Pydantic schemas for encrypted emotion inference and analysis."""
from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class EncryptedImageRequest(BaseModel):
    ciphertext: str = Field(..., description="Serialized encrypted image payload")
    key_id: str = Field(..., description="Logical identifier of the client key")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional client-side metadata")


class EncryptedPredictionResponse(BaseModel):
    ciphertext: str
    date: date


class NDayAnalysisRequest(BaseModel):
    days: int | None = None


class EncryptedNDayAnalysisResponse(BaseModel):
    ciphertext: str
