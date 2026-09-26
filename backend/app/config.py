import logging
import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Named constant for the Gemini API key placeholder (avoids magic strings)
GEMINI_KEY_PLACEHOLDER = "your_gemini_api_key_here"

# Named constant for the insecure JWT default (avoids magic strings)
_INSECURE_JWT_DEFAULT = "insecure_default_secret_key_at_least_32_bytes_long"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "ClauseLens"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    # Gemini Models (Active Gemini 3.x & GA Embedding)
    GEMINI_API_KEY: str = ""
    GEMINI_FLASH_MODEL: str = "gemini-3.8-flash"
    GEMINI_PRO_MODEL: str = "gemini-3.8-flash"  # Free-tier default, upgradeable to gemini-3.1-pro
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Storage & Database
    DATABASE_URL: str = "sqlite:///./clauselens.db"
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # Security
    JWT_SECRET: str = _INSECURE_JWT_DEFAULT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    # Limits
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    RATE_LIMIT_PER_MINUTE: str = "30/minute"
    UPLOAD_RATE_LIMIT_PER_MINUTE: str = "10/minute"

    @property
    def has_gemini_key(self) -> bool:
        """Check if a real Gemini API key is configured (not placeholder or empty)."""
        return bool(self.GEMINI_API_KEY) and self.GEMINI_API_KEY != GEMINI_KEY_PLACEHOLDER

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip().rstrip("/") for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [origin.rstrip("/") if isinstance(origin, str) else origin for origin in v]
        return v


settings = Settings()

# Runtime warnings for insecure defaults (logged once at import time)
if settings.JWT_SECRET == _INSECURE_JWT_DEFAULT:
    logger.warning(
        "JWT_SECRET is using the insecure default. Set a strong random secret "
        "via the JWT_SECRET environment variable before deploying to production."
    )
