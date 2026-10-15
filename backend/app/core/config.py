"""Centralised configuration, read from environment variables / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT / ".env"), str(ROOT / "backend" / ".env")), extra="ignore"
    )

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    allow_registration: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    google_client_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b-instruct"
    ollama_timeout_seconds: float = 180.0
    ollama_num_predict: int = 700
    ai_max_retries: int = 1

    max_upload_mb: int = 5
    max_import_rows: int = 5000

    @field_validator("jwt_secret")
    @classmethod
    def _secret_len(cls, v: str) -> str:
        if len(v) < 16 or v.startswith("CHANGE_ME"):
            raise ValueError("JWT_SECRET must be set to a random string of at least 16 characters")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
