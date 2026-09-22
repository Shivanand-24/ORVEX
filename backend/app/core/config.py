import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables or .env file."""

    APP_NAME: str = "ORVEX API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173"]
    LOG_LEVEL: str = "INFO"

    # Database Configuration (PostgreSQL 16)
    DATABASE_URL: str = "postgresql+asyncpg://orvex_user:orvex_dev_secret@localhost:5432/orvex_db"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://orvex_user:orvex_dev_secret@localhost:5432/orvex_db"

    # LLM Gateway Configuration
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: Union[str, None] = None
    LLM_API_BASE_URL: Union[str, None] = None
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
