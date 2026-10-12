from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FIN-SHIELD"
    environment: str = "development"
    # Production (Render): set DATABASE_URL to a postgresql:// connection string
    # via the Render environment variable panel.  The /tmp fallback lets the
    # process start in environments where no DATABASE_URL is configured, but
    # data stored there is ephemeral and will be lost on restart.
    database_url: str = "sqlite:////tmp/finshield.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    similarity_threshold: float = 0.72
    # Writable scratch space available on Render, Vercel serverless, and locally.
    upload_dir: str = "/tmp/finshield_uploads"
    max_upload_bytes: int = 5 * 1024 * 1024
    shared_entity_alert_threshold: int = 3
    high_risk_min_score: int = 50
    log_level: str = "INFO"
    tesseract_cmd: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
