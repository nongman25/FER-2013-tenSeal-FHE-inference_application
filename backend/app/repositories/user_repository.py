"""Repository for user persistence and retrieval."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import UserCreate


class UserRepository:
    def create_user(self, db: Session, user_create: UserCreate, password_hash: str) -> User:
        user = User(user_id=user_create.user_id, password=password_hash, email=user_create.email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_by_user_id(self, db: Session, user_id: str) -> User | None:
        return db.query(User).filter(User.user_id == user_id).first()

    def verify_credentials(self, db: Session, user_id: str, password: str) -> User | None:
        user = self.get_by_user_id(db, user_id)
        if user and verify_password(password, user.password):
            return user
        return None
