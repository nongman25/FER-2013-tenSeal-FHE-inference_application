"""Application settings using environment variables."""
from __future__ import annotations

from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Environment-driven configuration for the FastAPI backend."""

    EMOTION_DB_HOST: str = Field("localhost", env="EMOTION_DB_HOST")
    EMOTION_DB_PORT: int = Field(3306, env="EMOTION_DB_PORT")
    EMOTION_DB_NAME: str = Field("emotiondb", env="EMOTION_DB_NAME")
    EMOTION_DB_USER: str = Field("root", env="EMOTION_DB_USER")
    EMOTION_DB_PASSWORD: str = Field("0524", env="EMOTION_DB_PASSWORD")
    EMOTION_DB_CHARSET: str = Field("utf8mb4", env="EMOTION_DB_CHARSET")
    EMOTION_DB_TIMEZONE: str = Field("Asia/Seoul", env="EMOTION_DB_TIMEZONE")

    JWT_SECRET_KEY: str = Field("dev-secret-key-change-me", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    EMOTION_ANALYSIS_DAYS: int = Field(10, env="EMOTION_ANALYSIS_DAYS")

    class Config:
        env_file = ".env"
        case_sensitive = False

    def sqlalchemy_url(self) -> str:
        """Build a SQLAlchemy URL for MySQL using pymysql driver."""
        return (
            f"mysql+pymysql://{self.EMOTION_DB_USER}:{self.EMOTION_DB_PASSWORD}"
            f"@{self.EMOTION_DB_HOST}:{self.EMOTION_DB_PORT}/{self.EMOTION_DB_NAME}"
            f"?charset={self.EMOTION_DB_CHARSET}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance to avoid re-parsing env."""
    return Settings()


settings = get_settings()
