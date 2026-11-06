"""СЗЧ (самовільне залишення частини) command implementation."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, get_session
from militarylaw_bot.bot.handlers import track_stats
from militarylaw_bot.bot.unified_keyboards import result_actions, szch_first_time

logger = logging.getLogger(__name__)

FIRST_TIME = "Так, вперше"
NOT_FIRST_TIME = "Ні, не вперше"


async def show_szch_first_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show the only SZCH question."""
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SZCH_FIRST_TIME_QUESTION,
        reply_markup=szch_first_time(),
        parse_mode="HTML",
    )
    return "szch_first_time"


async def start_szch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start SZCH from the main menu."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    session.answers.clear()
    session.push_history()
    session.current_command = CommandType.SZCH
    session.step = "szch_first_time"
    track_stats(chat_id, "szch", "started")
    return await show_szch_first_time(update, context)


async def handle_szch_first_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle 'first SZCH or desertion under martial law' question."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == FIRST_TIME:
        parts = list(texts.SZCH_FIRST_TIME_RESULT)
    elif text == NOT_FIRST_TIME:
        parts = [texts.SZCH_NOT_FIRST_TIME_RESULT]
    else:
        await update.message.reply_text("❌ Виберіть один з варіантів")
        return "szch_first_time"

    session.answers["first_time"] = text
    session.push_history()
    session.step = "szch_result"
    parts[0] = texts.SZCH_RESULT_HEADER + parts[0]
    parts[-1] += texts.CLOSING_NOTE

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        await update.message.reply_text(
            part,
            reply_markup=result_actions() if is_last else None,
            parse_mode="HTML",
        )
    return "szch_result"


async def handle_szch_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle result screen - just stay on result."""
    return "szch_result"
