"""СЗЧ (Служба без дозволу) command implementation."""

from __future__ import annotations

import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, get_session
from militarylaw_bot.bot.unified_keyboards import (
    szch_formation, szch_yes_no, szch_awol_date,
    szch_return_type, szch_zsu_submission, szch_dsst_submission,
    szch_general_arrival, szch_consent, text_input_keyboard,
    result_actions,
)

logger = logging.getLogger(__name__)






async def handle_szch_formation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle formation selection."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()
    valid_options = ["ЗСУ", "НГУ", "ДПСУ", "ДССТ"]
    if text not in valid_options:
        await update.message.reply_text("❌ Виберіть один з варіантів")
        return "szch_formation"

    session.answers["formation"] = text
    session.push_history()
    session.step = "szch_want_return"

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SZCH_WANT_RETURN,
        reply_markup=szch_yes_no(),
        parse_mode="HTML",
    )
    return "szch_want_return"


async def handle_szch_want_return(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle 'do you want to return' question."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()
    if text not in ["Так", "Ні"]:
        await update.message.reply_text("❌ Виберіть Так або Ні")
        return "szch_want_return"

    session.answers["want_return"] = text
    session.push_history()

    if text == "Ні":
        session.step = "szch_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SZCH_DO_NOT_WANT_RETURN,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "szch_result"

    session.step = "szch_first_time_awol"
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SZCH_FIRST_TIME_AWOL,
        reply_markup=szch_yes_no(),
        parse_mode="HTML",
    )
    return "szch_first_time_awol"


async def handle_szch_first_time_awol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle 'is this first AWOL' question."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    text = update.message.text.strip()
    if text not in ["Так", "Ні"]:
        await update.message.reply_text("❌ Виберіть Так або Ні")
        return "szch_first_time_awol"

    session.answers["first_time_awol"] = text
    session.push_history()

    if text == "Ні":
        session.step = "szch_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SZCH_NOT_FIRST_TIME_RESULT,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "szch_result"

    session.step = "szch_awol_date"
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SZCH_AWOL_DATE,
        reply_markup=szch_awol_date(),
        parse_mode="HTML",
    )
    return "szch_awol_date"


async def handle_szch_awol_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle AWOL start date."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    text = update.message.text.strip()
    valid_options = ["До 12.06.2026 включно", "З 13.06.2026", "Не знаю"]
    if text not in valid_options:
        await update.message.reply_text("❌ Виберіть один з варіантів")
        return "szch_awol_date"

    session.answers["awol_date"] = text
    session.push_history()

    if text == "Не знаю":
        session.step = "szch_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SZCH_NEED_DATE,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "szch_result"

    session.step = "szch_return_type"
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SZCH_RETURN_TYPE,
        reply_markup=szch_return_type(),
        parse_mode="HTML",
    )
    return "szch_return_type"


async def handle_szch_return_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle return type choice (simplified or general)."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    text = update.message.text.strip()
    valid_options = ["Спрощений порядок повернення", "Загальний порядок повернення"]
    if text not in valid_options:
        await update.message.reply_text("❌ Виберіть один з варіантів")
        return "szch_return_type"

    session.answers["return_type"] = text
    session.push_history()

    if text == "Загальний порядок повернення":
        session.step = "szch_general_arrival"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SZCH_GENERAL_ARRIVAL,
            reply_markup=szch_general_arrival(),
            parse_mode="HTML",
        )
        return "szch_general_arrival"

    formation = session.answers.get("formation", "")
    session.step = "szch_simplified_submission"

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    if formation == "ДПСУ":
        session.step = "result"
        await update.message.reply_text(
            texts.SZCH_DPSU_SIMPLIFIED_UNAVAILABLE,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "szch_result"

    if formation == "ДССТ":
        keyboard = szch_dsst_submission()
    else:
        keyboard = szch_zsu_submission()

    await update.message.reply_text(
        texts.SZCH_ZSU_SIMPLIFIED_SUBMISSION,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return "szch_simplified_submission"


async def handle_szch_simplified_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle simplified submission method."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    text = update.message.text.strip()
    session.answers["submission_method"] = text
    session.push_history()
    session.step = "szch_erdr"

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SZCH_ERDR_QUESTION,
        reply_markup=szch_yes_no(),
        parse_mode="HTML",
    )
    return "szch_erdr"


async def handle_szch_erdr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle ERDR question."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    text = update.message.text.strip()
    if text not in ["Так", "Ні", "Не знаю"]:
        await update.message.reply_text("❌ Виберіть один з варіантів")
        return "szch_erdr"

    session.answers["erdr"] = text
    session.push_history()
    session.step = "result"

    if text == "Так":
        result_text = texts.SZCH_ERDR_YES
    elif text == "Ні":
        result_text = texts.SZCH_ERDR_NO
    else:
        result_text = texts.SZCH_ERDR_UNKNOWN

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        result_text,
        reply_markup=result_actions(),
        parse_mode="HTML",
    )
    return "szch_result"


async def handle_szch_general_arrival(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle general arrival location."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    text = update.message.text.strip()
    session.answers["arrival_location"] = text
    session.push_history()
    session.step = "szch_commander_consent"

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SZCH_COMMANDER_CONSENT,
        reply_markup=szch_consent(),
        parse_mode="HTML",
    )
    return "szch_commander_consent"


async def handle_szch_commander_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle commander consent question."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    text = update.message.text.strip()
    if text not in ["Так", "Ні", "Не знаю"]:
        await update.message.reply_text("❌ Виберіть один з варіантів")
        return "szch_commander_consent"

    session.answers["commander_consent"] = text
    session.push_history()
    session.step = "result"

    if text == "Так":
        result_text = texts.SZCH_COMMANDER_CONSENT_YES
    elif text == "Ні":
        result_text = texts.SZCH_COMMANDER_CONSENT_NO
    else:
        result_text = texts.SZCH_COMMANDER_CONSENT_UNKNOWN

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        result_text,
        reply_markup=result_actions(),
        parse_mode="HTML",
    )
    return "szch_result"


async def handle_szch_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle result screen - just stay on result."""
    return "szch_result"
