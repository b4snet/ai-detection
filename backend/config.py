"""SENTINEL AI - central configuration.

All runtime settings are read from environment variables / .env file.
Defaults are chosen so the platform boots instantly on a laptop with
zero configuration.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------- paths ----
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
DB_DIR = BASE_DIR / "database"
REPORT_DIR = BASE_DIR / "reports"
MODEL_DIR = BASE_DIR / "ai_models"
DATA_DIR = BASE_DIR / "backend" / "sample_data"

for _d in (UPLOAD_DIR, DB_DIR, REPORT_DIR, MODEL_DIR, DATA_DIR):
    _d.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    sentinel_host: str = "0.0.0.0"
    sentinel_port: int = 8000
    sentinel_debug: bool = True

    # Database
    database_url: str = f"sqlite:///{DB_DIR.as_posix()}/sentinel.db"

    # Local AI
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    ollama_vision_model: str = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:7b")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "8"))

    # OSINT
    gdelt_enabled: bool = True
    newsapi_key: str = ""
    opencage_api_key: str = ""

    # Feature toggles
    simulation_mode: str = "auto"  # auto | on | off
    vision_enabled: bool = True
    osint_enabled: bool = True
    cache_age_hours: int = 48

    # Paths
    upload_dir: str = str(UPLOAD_DIR)
    report_dir: str = str(REPORT_DIR)
    model_dir: str = str(MODEL_DIR)
    data_dir: str = str(DATA_DIR)

    @property
    def uploads(self) -> Path:
        return Path(self.upload_dir)

    @property
    def reports(self) -> Path:
        return Path(self.report_dir)

    @property
    def models(self) -> Path:
        return Path(self.model_dir)

    @property
    def data(self) -> Path:
        return Path(self.data_dir)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.uploads.mkdir(parents=True, exist_ok=True)
    s.reports.mkdir(parents=True, exist_ok=True)
    s.models.mkdir(parents=True, exist_ok=True)
    return s


settings = get_settings()
