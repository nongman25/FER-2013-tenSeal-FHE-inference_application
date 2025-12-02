"""FastAPI application factory wiring routes, services, and shared state."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_auth, routes_emotion, routes_health
from app.core.db import Base, engine
from app.models import emotion_data, user  # noqa: F401 - ensure models are registered
from app.repositories.emotion_data_repository import EmotionDataRepository
from app.repositories.user_repository import UserRepository
from app.services.analysis_service import AnalysisService
from app.services.auth_service import AuthService
from app.services.emotion_service import EmotionService
from app.services.he_service import HEEmotionEngine


def create_app() -> FastAPI:
    app = FastAPI(title="FHE Emotion Prototype", version="0.1.0")

    # Initialize persistence and services
    Base.metadata.create_all(bind=engine)
    he_engine = HEEmotionEngine()
    user_repo = UserRepository()
    emotion_repo = EmotionDataRepository()

    app.state.auth_service = AuthService(user_repo)
    app.state.emotion_service = EmotionService(emotion_repo, he_engine)
    app.state.analysis_service = AnalysisService(emotion_repo, he_engine)
    app.state.he_engine = he_engine

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_auth.router)
    app.include_router(routes_emotion.router)
    app.include_router(routes_health.router)

    return app


app = create_app()
