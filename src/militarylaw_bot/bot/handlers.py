"""Core handlers for bot commands."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import get_session
from militarylaw_bot.bot.unified_keyboards import build_main_menu_keyboard
from militarylaw_bot.db import UserDatabase

logger = logging.getLogger(__name__)

_user_db: UserDatabase | None = None


def set_user_db(user_db: UserDatabase) -> None:
    """Set the global user database for tracking."""
    global _user_db
    _user_db = user_db


def _track_user(update: Update) -> None:
    """Track user interaction."""
    if _user_db is None:
        return
    if update.message and update.message.chat_id:
        _user_db.track_user(update.message.chat_id)
    elif update.callback_query and update.callback_query.message:
        _user_db.track_user(update.callback_query.message.chat_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - show welcome message and main menu."""
    _track_user(update)

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
