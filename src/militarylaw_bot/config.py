"""Environment-driven configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    persistence_path: str
    webhook_url: str | None
    webhook_port: int
    webhook_path: str
    webhook_secret: str | None
    admin_chat_id: int


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

    webhook_url = os.environ.get("WEBHOOK_URL") or None
    webhook_secret = os.environ.get("WEBHOOK_SECRET") or None

    if webhook_url and not webhook_secret:
        raise RuntimeError("WEBHOOK_SECRET must be set when WEBHOOK_URL is configured")

    admin_chat_id = os.environ.get("ADMIN_CHAT_ID")
    if not admin_chat_id:
        raise RuntimeError("ADMIN_CHAT_ID environment variable is not set")

    return Settings(
        bot_token=bot_token,
        persistence_path=os.environ.get("PERSISTENCE_PATH", "/app/data/bot_state.pickle"),
        webhook_url=webhook_url,
        webhook_port=int(os.environ.get("WEBHOOK_PORT", "8443")),
        webhook_path=os.environ.get("WEBHOOK_PATH", "/militarylaw/webhook"),
        webhook_secret=webhook_secret,
        admin_chat_id=int(admin_chat_id),
    )
