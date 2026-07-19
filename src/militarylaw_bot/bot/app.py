"""Application entry point: builds and runs the Telegram bot."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, PicklePersistence

from militarylaw_bot.bot import handlers
from militarylaw_bot.bot.commands import register_commands
from militarylaw_bot.bot.command_stats import set_user_db as set_stats_db
from militarylaw_bot.bot.middleware import UserTrackingHandler
from militarylaw_bot.bot.utils import get_data_path
from militarylaw_bot.config import load_settings
from militarylaw_bot.db import UserDatabase

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    logger.info("Building application...")
    settings = load_settings()
    persistence = PicklePersistence(filepath=settings.persistence_path)

    application = (
        Application.builder()
        .token(settings.bot_token)
        .persistence(persistence)
        .concurrent_updates(True)
        .build()
    )
    logger.info("✅ Application instance created")

    # Initialize user database
    db_path = str(get_data_path("users.json"))
    user_db = UserDatabase(db_path=db_path)
    handlers.set_user_db(user_db)
    set_stats_db(user_db)
    logger.info(f"✅ User database initialized: {db_path}")

    # Add tracking handler first (group -1 runs before all others)
    application.add_handler(UserTrackingHandler(user_db), group=-1)
    logger.info("✅ Tracking handler added")

    # Register all commands and handlers
    logger.info("About to register commands...")
    register_commands(application)
    logger.info("✅ Commands registered")

    return application


def main() -> None:
    application = build_application()
    settings = load_settings()

    if settings.webhook_url:
        logger.info("Bot starting (webhook mode)...")
        application.run_webhook(
            listen="0.0.0.0",
            port=settings.webhook_port,
            url_path=settings.webhook_path,
            webhook_url=settings.webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        logger.info("Bot starting (polling mode)...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
