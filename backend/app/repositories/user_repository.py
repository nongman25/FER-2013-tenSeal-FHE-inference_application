"""Repository for user persistence and retrieval."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserCreate


class UserRepository:
    def create_user(self, db: Session, user_create: UserCreate, password_hash: str) -> User:
        user = User(user_id=user_create.user_id, password=password_hash, email=user_create.email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_by_user_id(self, db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.user_id == user_id).first()
