"""Pydantic schemas for authentication flows."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    user_id: str
    password: str
    email: EmailStr | None = None


class UserLogin(BaseModel):
    user_id: str
    password: str


class UserOut(BaseModel):
    user_id: str
    email: EmailStr | None = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
