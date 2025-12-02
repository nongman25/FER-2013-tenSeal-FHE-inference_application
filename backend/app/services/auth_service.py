"""Authentication service handling registration and login."""
from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserOut


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register_user(self, db: Session, user_create: UserCreate) -> UserOut:
        existing = self.user_repository.get_by_user_id(db, user_create.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )
        password_hash = get_password_hash(user_create.password)
        user = self.user_repository.create_user(db, user_create, password_hash)
        return UserOut.from_orm(user)

    def authenticate_user(self, db: Session, user_id: str, password: str):
        user = self.user_repository.get_by_user_id(db, user_id)
        if user and verify_password(password, user.password):
            return user
        return None

    def issue_access_token(self, subject: str) -> str:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(data={"sub": subject}, expires_delta=expires_delta)
