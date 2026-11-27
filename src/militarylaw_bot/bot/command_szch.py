"""СЗЧ (самовільне залишення частини) command implementation.

Flow: first SZCH? → (first time) will you find a place of service yourself? → result.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, GlobalSession, get_session
from militarylaw_bot.bot.handlers import track_stats
from militarylaw_bot.bot.unified_keyboards import (
    result_actions,
    szch_first_time,
    szch_self_placement,
)

logger = logging.getLogger(__name__)

FIRST_TIME = "Так, вперше"
NOT_FIRST_TIME = "Ні, не вперше"
YES = "Так"
NO = "Ні"

# Question screens: step -> (text, keyboard builder)
_QUESTIONS = {
    "szch_first_time": (texts.SZCH_FIRST_TIME_QUESTION, szch_first_time),
    "szch_self_placement": (texts.SZCH_SELF_PLACEMENT_QUESTION, szch_self_placement),
}


async def render_szch_step(update: Update, context: ContextTypes.DEFAULT_TYPE, step: str) -> str:
    """Show a question screen (used for forward moves and back navigation)."""
    text, keyboard = _QUESTIONS[step]
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    await update.message.reply_text(text, reply_markup=keyboard(), parse_mode="HTML")
    return step


async def start_szch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start SZCH from the main menu."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    session.answers.clear()
    session.push_history()
    session.current_command = CommandType.SZCH
    session.step = "szch_first_time"
    track_stats(chat_id, "szch", "started")
    return await render_szch_step(update, context, session.step)


async def _invalid_choice(update: Update, step: str) -> str:
    """Explain that a button is expected and show the buttons again."""
    _, keyboard = _QUESTIONS[step]
    await update.message.reply_text(
        texts.INVALID_CHOICE, reply_markup=keyboard(), parse_mode="HTML"
    )
    return step


async def _send_result(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: GlobalSession, parts: list[str]
) -> str:
    """Send a result as one or more messages; the keyboard goes with the last one."""
    session.step = "szch_result"
    parts = list(parts)
    parts[0] = texts.SZCH_RESULT_HEADER + parts[0]
    parts[-1] += texts.CLOSING_NOTE

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        await update.message.reply_text(
            part,
            reply_markup=result_actions() if is_last else None,
            parse_mode="HTML",
        )
    return "szch_result"


async def handle_szch_first_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle 'first SZCH or desertion under martial law' question."""
    session = get_session(update.effective_chat.id)
    text = update.message.text.strip()

    if text not in (FIRST_TIME, NOT_FIRST_TIME):
        return await _invalid_choice(update, "szch_first_time")

    session.answers["first_time"] = text
    session.push_history()
    if text == NOT_FIRST_TIME:
        return await _send_result(update, context, session, [texts.SZCH_NOT_FIRST_TIME_RESULT])
    session.step = "szch_self_placement"
    return await render_szch_step(update, context, session.step)


async def handle_szch_self_placement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle 'will you find a place of service yourself' question."""
    session = get_session(update.effective_chat.id)
    text = update.message.text.strip()

    if text not in (YES, NO):
        return await _invalid_choice(update, "szch_self_placement")

    session.answers["self_placement"] = text
    session.push_history()
    if text == YES:
        return await _send_result(update, context, session, texts.SZCH_FIRST_TIME_RESULT)
    return await _send_result(update, context, session, [texts.SZCH_NO_SELF_PLACEMENT_RESULT])


async def handle_szch_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle result screen - just stay on result."""
    return "szch_result"
