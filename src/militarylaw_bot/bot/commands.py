"""Bot command registration and setup."""

from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from militarylaw_bot.bot.command_prydatnist import handle_legacy_callback
from militarylaw_bot.bot.command_stats import handle_stats
from militarylaw_bot.bot.unified_conversation import build_unified_conversation

logger = logging.getLogger(__name__)


def register_commands(application: Application) -> None:
    """Register all bot commands and handlers."""
    logger.info("Registering bot commands...")

    # Unified conversation (all commands, menu, /start, /prydatnist)
    application.add_handler(build_unified_conversation())
    logger.info("✅ Unified conversation")

    # Inline buttons left in chats by the old prydatnist version
    application.add_handler(CallbackQueryHandler(handle_legacy_callback, pattern=r"^pryd_"))

    # Commands
    application.add_handler(CommandHandler("stats", handle_stats))
    logger.info("✅ Commands registered")

    logger.info("✅ All handlers registered")
