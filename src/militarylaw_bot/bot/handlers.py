"""Core handlers for bot commands."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import get_session
from militarylaw_bot.bot.unified_keyboards import build_main_menu_keyboard
from militarylaw_bot.db import StatisticsTracker

logger = logging.getLogger(__name__)

_stats_tracker: StatisticsTracker | None = None


def set_stats_tracker(stats_tracker: StatisticsTracker) -> None:
    """Set the global statistics tracker."""
    global _stats_tracker
    _stats_tracker = stats_tracker


def track_stats(user_id: int, command: str, action: str, step: str | None = None) -> None:
    """Track user statistics."""
    if _stats_tracker is None:
        return
    _stats_tracker.track_action(user_id, command, action, step)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - show welcome message and main menu."""
    # Reset global session
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    session.reset_to_menu()

    # Send WELCOME message with command menu
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.WELCOME,
        reply_markup=build_main_menu_keyboard(),
        parse_mode="HTML"
    )
