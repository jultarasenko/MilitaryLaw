"""Application entry point: builds and runs the Telegram bot."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, PicklePersistence

from militarylaw_bot.bot import handlers
from militarylaw_bot.bot.conversation import build_vidstrochka_conversation
from militarylaw_bot.config import load_settings

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    settings = load_settings()
    persistence = PicklePersistence(filepath=settings.persistence_path)

    application = Application.builder().token(settings.bot_token).persistence(persistence).build()
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(build_vidstrochka_conversation())
    return application


def main() -> None:
    application = build_application()
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
