"""Environment-driven configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    persistence_path: str


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

    return Settings(
        bot_token=bot_token,
        persistence_path=os.environ.get("PERSISTENCE_PATH", "/app/data/bot_state.pickle"),
    )
