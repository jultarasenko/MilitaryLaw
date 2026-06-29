"""Application entry point: builds and runs the Telegram bot."""

from __future__ import annotations

import logging
import os
from functools import partial

from telegram import Update
from telegram.ext import Application, CommandHandler, PicklePersistence

from militarylaw_bot.bot import handlers
from militarylaw_bot.bot.conversation import build_vidstrochka_conversation
from militarylaw_bot.bot.middleware import UserTrackingHandler
from militarylaw_bot.config import load_settings
from militarylaw_bot.db import UserDatabase
from militarylaw_bot.jobs import send_daily_stats

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Global storage for job setup
_job_config: dict = {}


def build_application() -> Application:
    global _job_config

    settings = load_settings()
    persistence = PicklePersistence(filepath=settings.persistence_path)

    application = (
        Application.builder()
        .token(settings.bot_token)
        .persistence(persistence)
        .concurrent_updates(True)
        .build()
    )

    # Initialize user database - use Docker path if available
    db_path = "/app/data/users.json" if os.path.exists("/app/data") else "data/users.json"
    user_db = UserDatabase(db_path=db_path)
    handlers.set_user_db(user_db)

    # Add tracking handler first (group -1 runs before all others)
    application.add_handler(UserTrackingHandler(user_db), group=-1)

    # Add handlers
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(build_vidstrochka_conversation())

    # Store for job setup in main()
    _job_config = {"settings": settings, "user_db": user_db}

    return application


def main() -> None:
    application = build_application()
    settings = load_settings()

    # Schedule hourly stats job (every hour at :00)
    if application.job_queue is not None:
        user_db = _job_config["user_db"]
        application.job_queue.run_repeating(
            partial(send_daily_stats, application.bot, settings.admin_chat_id, user_db),
            interval=3600,  # Every hour (3600 seconds)
            first=0,  # Start immediately
            name="hourly_stats",
        )
        logger.info("Hourly stats job scheduled (every hour at :00)")

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
