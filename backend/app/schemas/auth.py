"""Pydantic schemas for authentication flows."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, validator

MAX_PASSWORD_LEN = 72  # bcrypt limit


class UserCreate(BaseModel):
    user_id: str
    password: str
    email: Optional[str] = None

    @validator("password")
    def password_length_guard(cls, v: str) -> str:
        if len(v.encode("utf-8")) > MAX_PASSWORD_LEN:
            raise ValueError(f"password must be <= {MAX_PASSWORD_LEN} bytes for bcrypt")
        return v


class UserLogin(BaseModel):
    user_id: str
    password: str

    @validator("password")
    def login_password_length_guard(cls, v: str) -> str:
        if len(v.encode("utf-8")) > MAX_PASSWORD_LEN:
            raise ValueError(f"password must be <= {MAX_PASSWORD_LEN} bytes for bcrypt")
        return v


class UserOut(BaseModel):
    user_id: str
    email: Optional[str] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
