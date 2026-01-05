"""Centralized project configuration loaded from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Settings:
    bot_token: str | None
    web_app_url: str
    database_url: str
    host: str
    port: int
    debug: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("BOT_TOKEN"),
        web_app_url=os.getenv("WEB_APP_URL", "http://localhost:8000"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./salon.db"),
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        debug=_to_bool(os.getenv("APP_DEBUG"), default=False),
    )


