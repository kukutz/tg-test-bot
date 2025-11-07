from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings, HttpUrl


class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_bot_username: str | None = None
    openai_api_key: str
    base_webapp_url: HttpUrl
    webhook_url: HttpUrl
    database_url: str = "sqlite+aiosqlite:///./bot.db"
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int | None = None
    environment: Literal["development", "production"] = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

