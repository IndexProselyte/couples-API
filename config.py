from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Security ──────────────────────────────────────────────────────────────
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days

    # ── Couple credentials (set once, never changed via API) ──────────────────
    hers_password: str
    his_password: str
    admin_password: str

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./couples.db"

    # ── File upload ───────────────────────────────────────────────────────────
    upload_dir: str = "uploads"
    base_url: str = "http://localhost:8000"
    max_upload_bytes: int = 52_428_800  # 50 MB

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: List[str] = ["*"]

    # ── Misc ──────────────────────────────────────────────────────────────────
    enable_docs: bool = False

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
