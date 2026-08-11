"""Bot command registration and setup."""

from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from militarylaw_bot.bot.command_stats import handle_stats
from militarylaw_bot.bot.command_prydatnist import handle_prydatnist, handle_prydatnist_callback, handle_keyword_input
from militarylaw_bot.bot.unified_conversation import build_unified_conversation

logger = logging.getLogger(__name__)


def register_commands(application: Application) -> None:
    """Register all bot commands and handlers."""
    logger.info("Registering bot commands...")

    # ===== Unified Conversation (all commands: menu, vidstrochka, szch, /start) =====
    logger.info("Registering unified conversation...")
    application.add_handler(build_unified_conversation())
    logger.info("✅ Registered unified conversation")

    # ===== Callback Handlers =====
    logger.info("Registering pryd_* callback handler...")
    callback_handler = CallbackQueryHandler(
        callback=handle_prydatnist_callback,
        pattern=r"^pryd_"
    )
    application.add_handler(callback_handler)
    logger.info("✅ Registered pryd_* callback handler")

    # ===== /stats Command =====
    application.add_handler(CommandHandler("stats", handle_stats))
    logger.info("✅ Registered /stats")

    # ===== /prydatnist Command =====
    logger.info("Registering /prydatnist command handler...")
    application.add_handler(CommandHandler("prydatnist", handle_prydatnist))
    logger.info("✅ Registered /prydatnist command handler")

    # ===== Text input for prydatnist keyword search =====
    logger.info("Registering keyword search text handler...")
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_keyword_input)
    application.add_handler(text_handler)
    logger.info("✅ Registered keyword search text handler")

    logger.info("✅ All commands registered successfully")
