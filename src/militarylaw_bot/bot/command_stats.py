"""Implementation of /stats command."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from militarylaw_bot.config import load_settings
from militarylaw_bot.jobs.daily_stats import send_stats

logger = logging.getLogger(__name__)

# Global reference to user database (set by app.py)
_user_db = None


def set_user_db(user_db) -> None:
    """Set the global user database reference."""
    global _user_db
    _user_db = user_db


async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - admin only statistics.

    Sends daily statistics (user activity, usage patterns) to admin users.
    """
    settings = load_settings()
    logger.info(f"User {update.message.chat_id} requested /stats")

    # Check if user is admin
    if update.message.chat_id not in settings.admin_chat_ids:
        logger.warning(f"Non-admin {update.message.chat_id} tried to access /stats")
        await update.message.reply_text("⛔ Ця команда доступна тільки адміністратору")
        return

    # Send stats to requesting admin
    logger.info(f"Sending stats to admin {update.message.chat_id}")
    await send_stats(context.bot, update.message.chat_id, _user_db)
