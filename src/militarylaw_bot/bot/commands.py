"""Bot command registration and setup."""

from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, filters

from militarylaw_bot.bot import handlers
from militarylaw_bot.bot.command_stats import handle_stats
from militarylaw_bot.bot.command_prydatnist import handle_prydatnist, handle_prydatnist_callback
from militarylaw_bot.bot.command_vidstrochka import get_vidstrochka_conversation

logger = logging.getLogger(__name__)


def register_commands(application: Application) -> None:
    """Register all bot commands and handlers.

    Handler registration order is critical:
    1. Callback-specific handlers (most specific first)
    2. Conversation handlers (less specific)
    3. Basic commands
    """
    logger.info("Registering bot commands...")

    # ===== Callback Handlers (MUST come FIRST, in higher priority group) =====
    logger.info("Registering pryd_* callback handler in group 0...")
    callback_handler = CallbackQueryHandler(
        callback=handle_prydatnist_callback,
        pattern=r"^pryd_"
    )
    application.add_handler(callback_handler, group=0)
    logger.info("✅ Registered pryd_* callback handler in group 0")

    # ===== /vidstrochka Conversation =====
    logger.info("Registering /vidstrochka conversation in group 1...")
    application.add_handler(get_vidstrochka_conversation(), group=1)
    logger.info("✅ Registered /vidstrochka conversation in group 1")

    # ===== Basic Commands =====
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("stats", handle_stats))
    logger.info("✅ Registered /start, /stats")

    # ===== /prydatnist Command =====
    logger.info("Registering /prydatnist command handler...")
    application.add_handler(CommandHandler("prydatnist", handle_prydatnist))
    logger.info("✅ Registered /prydatnist command handler")

    logger.info("✅ All commands registered successfully")
