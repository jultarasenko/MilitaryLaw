"""Bot command registration and setup."""

from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from militarylaw_bot.bot.command_stats import handle_stats
from militarylaw_bot.bot.command_prydatnist import handle_prydatnist_callback
from militarylaw_bot.bot.command_prydatnist_handlers import handle_prydatnist_start
from militarylaw_bot.bot.unified_conversation import build_unified_conversation

logger = logging.getLogger(__name__)


def register_commands(application: Application) -> None:
    """Register all bot commands and handlers."""
    logger.info("Registering bot commands...")

    # Unified conversation (vidstrochka, szch, menu, /start)
    application.add_handler(build_unified_conversation())
    logger.info("✅ Unified conversation")

    # Prydatnist inline menu callbacks
    application.add_handler(CallbackQueryHandler(
        callback=handle_prydatnist_callback,
        pattern=r"^pryd_"
    ))
    logger.info("✅ Prydatnist callbacks")

    # Commands
    application.add_handler(CommandHandler("prydatnist", handle_prydatnist_start))
    application.add_handler(CommandHandler("stats", handle_stats))
    logger.info("✅ Commands registered")

    logger.info("✅ All handlers registered")
