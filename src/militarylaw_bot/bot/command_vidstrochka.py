"""Unified handlers for /vidstrochka command using global session."""

from __future__ import annotations

import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, get_session
from militarylaw_bot.bot.unified_keyboards import (
    vidstrochka_gate_2022,
    vidstrochka_contract_status,
    vidstrochka_contract_extension,
    vidstrochka_contract_type,
    vidstrochka_contract_term_768,
    vidstrochka_age_at_signing,
    vidstrochka_contract_term,
    vidstrochka_discharged_before_768,
    vidstrochka_registration_question,
    text_input_keyboard,
    result_actions,
    result_actions_with_contract,
)

logger = logging.getLogger(__name__)


async def _invalid_choice(update: Update, keyboard) -> None:
    """Explain that a button is expected and show the buttons again."""
    await update.message.reply_text(texts.INVALID_CHOICE, reply_markup=keyboard, parse_mode="HTML")


async def _invalid_number(update: Update) -> None:
    await update.message.reply_text(
        texts.INVALID_NUMBER, reply_markup=text_input_keyboard(), parse_mode="HTML"
    )


async def _send_deferral_result(update: Update, context: ContextTypes.DEFAULT_TYPE, session, result_text: str) -> str:
    """Send a result that grants a deferral and offer info on how to register it."""
    session.step = "vidstrochka_result"
    # Set after push_history so going back drops it
    session.answers["has_deferral"] = True
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    await update.message.reply_text(texts.with_closing_note(result_text), parse_mode="HTML")
    await update.message.reply_text(
        texts.REGISTRATION_QUESTION,
        reply_markup=vidstrochka_registration_question(),
        parse_mode="HTML",
    )
    return "vidstrochka_result"


def calculate_deferral_153_detailed(answers: dict) -> str:
    """Calculate deferral period for KMU 153 contract (25+ years old).

    Components for 25+ years old:
    - 6 months base
    - 1 month per 30 days combat
    """
    combat_periods = answers.get("combat_periods", 0)

    components = []
    total_months = 0

    # Base component - always 6 months
    a_months = 6
    components.append(f"• фіксованої частини відстрочки = {a_months} міс.")
    total_months += a_months

    # Combat periods component - 1 month per 30 days
    d_months = combat_periods * 1
    if d_months > 0:
        components.append(f"• по 1 місяцю за кожні 30 днів безпосередньої участі у бойових діях = {d_months} міс.")
    total_months += d_months

    # Format total (always in months)
    total_text = f"{total_months} міс."

    # Build result message
    result = "Відстрочка складатиметься з:\n"
    result += "\n".join(components)
    result += f"\n\nОрієнтовний загальний строк: {total_text}"

    return result


def calculate_deferral_768_detailed(answers: dict) -> str:
    """Calculate deferral period for KMU 768 contract with detailed breakdown.

    Components:
    A = 6 months
    Б = 3 months per 30 days combat
    В = 6 months per year service after 24.02.2022
    Г = 1 month per year service before 24.02.2022
    Д = 1 month per 30 days combat
    """
    term = answers.get("contract_term_768")
    combat_periods = answers.get("combat_periods", 0)
    service_since_2022 = answers.get("service_since_2022", 0)
    service_before_2022 = answers.get("service_before_2022", 0)

    components = []
    total_months = 0

    # Base component A - always 6 months
    a_months = 6
    components.append(f"• фіксованої частини відстрочки = {a_months} міс.")
    total_months += a_months

    if term == "6_months":
        # 6 месяцев: A + Б
        b_months = combat_periods * 3
        if b_months > 0:
            components.append(f"• по 3 місяці за кожен 30-денний період безпосередньої участі у бойових діях = {b_months} міс.")
        total_months += b_months

    elif term == "10_months":
        # 10 месяцев: A + Б + В + Г
        b_months = combat_periods * 3
        if b_months > 0:
            components.append(f"• по 3 місяці за кожен 30-денний період безпосередньої участі у бойових діях = {b_months} міс.")
        total_months += b_months

        v_months = service_since_2022 * 6
        if v_months > 0:
            components.append(f"• по 6 місяців за кожний рік військової служби з 24.02.2022 р. до укладення контракту = {v_months} міс.")
        total_months += v_months

        g_months = service_before_2022 * 1
        if g_months > 0:
            components.append(f"• по 1 місяцю за кожний рік безпосередньої військової служби до 24.02.2022 р. = {g_months} міс.")
        total_months += g_months

    elif term == "12_months":
        # 12 месяцев: A + Б + Г
        b_months = combat_periods * 3
        if b_months > 0:
            components.append(f"• по 3 місяці за кожен 30-денний період безпосередньої участі у бойових діях = {b_months} міс.")
        total_months += b_months

        g_months = service_before_2022 * 1
        if g_months > 0:
            components.append(f"• по 1 місяцю за кожний рік безпосередньої військової служби до 24.02.2022 р. = {g_months} міс.")
        total_months += g_months

    elif term == "24_months":
        # 24 месяца: A + Г + Д
        g_months = service_before_2022 * 1
        if g_months > 0:
            components.append(f"• по 1 місяцю за кожний рік безпосередньої військової служби до 24.02.2022 р. = {g_months} міс.")
        total_months += g_months

        d_months = combat_periods * 1
        if d_months > 0:
            components.append(f"• по 1 місяцю за кожні 30 днів безпосередньої участі у бойових діях = {d_months} міс.")
        total_months += d_months

    # Format total (always in months)
    total_text = f"{total_months} міс."

    # Build result message
    result = "Відстрочка складатиметься з:\n"
    result += "\n".join(components)
    result += f"\n\nОрієнтовний загальний строк: {total_text}"

    return result

async def handle_vidstrochka_gate_2022(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle gate 2022 answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "Так, до 24.02.2022 р.":
        session.answers["gate_2022"] = "before"
        session.push_history()
        session.step = "vidstrochka_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.NO_2022_CONTRACT,
            reply_markup=result_actions_with_contract(),
            parse_mode="HTML",
        )
        return "vidstrochka_result"

    elif text == "Ні, після 24.02.2022 р.":
        session.answers["gate_2022"] = "after"
        session.push_history()
        session.step = "vidstrochka_contract_status"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_CONTRACT_STATUS,
            reply_markup=vidstrochka_contract_status(),
            parse_mode="HTML",
        )
        return "vidstrochka_contract_status"

    elif text == "Тільки планую укласти контракт":
        session.answers["gate_2022"] = "planning"
        session.push_history()
        session.step = "vidstrochka_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.PLANNING_CONTRACT_DISCLAIMER,
            reply_markup=result_actions_with_contract(),
            parse_mode="HTML",
        )
        return "vidstrochka_result"

    else:
        await _invalid_choice(update, vidstrochka_gate_2022())
        return "vidstrochka_gate_2022"


async def handle_vidstrochka_contract_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle contract status answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "Так, на певний строк":
        session.answers["contract_status"] = "active"
        session.push_history()
        session.step = "vidstrochka_contract_extension"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_CONTRACT_EXTENSION,
            reply_markup=vidstrochka_contract_extension(),
            parse_mode="HTML",
        )
        return "vidstrochka_contract_extension"

    elif text == "Ні, до закінчення особливого періоду":
        session.answers["contract_status"] = "special_period"
        session.push_history()
        session.step = "vidstrochka_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SPECIAL_PERIOD_CONTRACT,
            reply_markup=result_actions_with_contract(),
            parse_mode="HTML",
        )
        return "vidstrochka_result"

    else:
        await _invalid_choice(update, vidstrochka_contract_status())
        return "vidstrochka_contract_status"


async def handle_vidstrochka_contract_extension(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle contract extension answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "Так, було":
        session.answers["contract_extension"] = "yes"
        session.push_history()
        session.step = "vidstrochka_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SPECIAL_PERIOD_CONTRACT,
            reply_markup=result_actions_with_contract(),
            parse_mode="HTML",
        )
        return "vidstrochka_result"

    elif text == "Ні, не було":
        session.answers["contract_extension"] = "no"
        session.push_history()
        session.step = "vidstrochka_contract_type"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_CONTRACT_TYPE,
            reply_markup=vidstrochka_contract_type(),
            parse_mode="HTML",
        )
        return "vidstrochka_contract_type"

    else:
        await _invalid_choice(update, vidstrochka_contract_extension())
        return "vidstrochka_contract_extension"


async def handle_vidstrochka_contract_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle contract type answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "Згідно Постанови КМУ №768 від 12.06.2026 р. (мотиваційний)":
        session.answers["contract_type"] = "kmu_768"
        session.push_history()
        session.step = "vidstrochka_contract_term_768"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_CONTRACT_TERM,
            reply_markup=vidstrochka_contract_term_768(),
            parse_mode="HTML",
        )
        return "vidstrochka_contract_term_768"

    elif text == "Згідно Постанови КМУ №153 від 11.02.2025 р. (18-24)":
        session.answers["contract_type"] = "kmu_153"
        session.push_history()
        session.step = "vidstrochka_contract_term"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_CONTRACT_TERM,
            reply_markup=vidstrochka_contract_term(),
            parse_mode="HTML",
        )
        return "vidstrochka_contract_term"

    elif text == "Інший (на загальних підставах)":
        session.answers["contract_type"] = "other"
        session.push_history()
        session.step = "vidstrochka_age_at_signing"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_AGE_AT_SIGNING,
            reply_markup=vidstrochka_age_at_signing(),
            parse_mode="HTML",
        )
        return "vidstrochka_age_at_signing"

    else:
        await _invalid_choice(update, vidstrochka_contract_type())
        return "vidstrochka_contract_type"


async def handle_vidstrochka_contract_term_768(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle contract term 768 answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    term_map = {
        "Від 6 міс.": "6_months",
        "10 міс.": "10_months",
        "12 міс.": "12_months",
        "24 міс.": "24_months",
    }

    if text in term_map:
        session.answers["contract_term_768"] = term_map[text]
        session.push_history()
        session.step = "vidstrochka_combat_periods"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.COMBAT_UNITS_PROMPT,
            reply_markup=text_input_keyboard(),
            parse_mode="HTML",
        )
        return "vidstrochka_combat_periods"
    else:
        await _invalid_choice(update, vidstrochka_contract_term_768())
        return "vidstrochka_contract_term_768"


async def handle_vidstrochka_age_at_signing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle age at signing answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "18-25 років":
        session.answers["age_at_signing"] = "18_25"
        session.push_history()
        session.step = "vidstrochka_contract_term"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_CONTRACT_TERM,
            reply_markup=vidstrochka_contract_term(),
            parse_mode="HTML",
        )
        return "vidstrochka_contract_term"

    elif text == "25 років та старше":
        session.answers["age_at_signing"] = "25_plus"
        session.push_history()
        session.step = "vidstrochka_discharged_before_768"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_DISCHARGED_BEFORE_768,
            reply_markup=vidstrochka_discharged_before_768(),
            parse_mode="HTML",
        )
        return "vidstrochka_discharged_before_768"

    else:
        await _invalid_choice(update, vidstrochka_age_at_signing())
        return "vidstrochka_age_at_signing"


async def handle_vidstrochka_contract_term(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle contract term answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "1 рік":
        session.answers["contract_term"] = "1_year"
        session.push_history()
        return await _send_deferral_result(update, context, session, texts.TWELVE_MONTHS_AFTER_DISCHARGE)

    elif text == "Більше 1 року":
        session.answers["contract_term"] = "more_than_1_year"
        session.push_history()
        session.step = "vidstrochka_discharged_before_768"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_DISCHARGED_BEFORE_768,
            reply_markup=vidstrochka_discharged_before_768(),
            parse_mode="HTML",
        )
        return "vidstrochka_discharged_before_768"

    else:
        await _invalid_choice(update, vidstrochka_contract_term())
        return "vidstrochka_contract_term"


async def handle_vidstrochka_discharged_before_768(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle discharge date for KMU 153 (25+ years old)."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "Так, до 16.06.2026 р.":
        # Discharged before 16.06.2026 - no deferral
        session.answers["discharged_before_768"] = "yes"
        session.push_history()
        session.step = "vidstrochka_result"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.with_closing_note(texts.NO_DEFERRAL),
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "vidstrochka_result"

    elif text == "Ні, після 16.06.2026 р.":
        # Not discharged before 16.06.2026 - need to ask about combat periods
        session.answers["discharged_before_768"] = "no"
        session.push_history()
        session.step = "vidstrochka_combat_periods"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.COMBAT_UNITS_PROMPT,
            reply_markup=text_input_keyboard(),
            parse_mode="HTML",
        )
        return "vidstrochka_combat_periods"

    else:
        await _invalid_choice(update, vidstrochka_discharged_before_768())
        return "vidstrochka_discharged_before_768"


async def handle_vidstrochka_combat_periods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle combat periods count answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if not text.isdigit() or int(text) < 0:
        await _invalid_number(update)
        return "vidstrochka_combat_periods"

    session.answers["combat_periods"] = int(text)
    session.push_history()

    # Determine next question based on contract term
    # 6 месяцев: А+Б (combat_periods + service_since_2022)
    # 10 месяцев: А+Б+В+Г (all questions)
    # 12 месяцев: А+Б+Г (combat_periods + service_since_2022 + ?)
    # 24 месяца: А+Г+Д (skip service_since_2022)

    term_768 = session.answers.get("contract_term_768")

    # Check if this is KMU 153 (age 25+, not discharged before 768)
    # For KMU 153: just calculate result
    if session.answers.get("discharged_before_768") == "no":
        result_text = calculate_deferral_153_detailed(session.answers)
        return await _send_deferral_result(update, context, session, result_text)

    # Ask only relevant questions based on term:
    # 6 месяцев (A+Б): только боевые периоды, потом результат
    # 10 месяцев (A+Б+В+Г): боевые периоды + годы после 2022 + годы до 2022
    # 12 месяцев (A+Б+Г): боевые периоды + годы до 2022
    # 24 месяца (A+Г+Д): боевые периоды + годы до 2022

    if term_768 == "6_months":
        # 6 месяцев: go to result (only need A + Б which we have)
        result_text = calculate_deferral_768_detailed(session.answers)
        return await _send_deferral_result(update, context, session, result_text)

    elif term_768 == "10_months":
        # 10 месяцев: ask service_since_2022
        session.step = "vidstrochka_service_since_2022"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SERVICE_SINCE_2022_PROMPT,
            reply_markup=text_input_keyboard(),
            parse_mode="HTML",
        )
        return "vidstrochka_service_since_2022"

    else:
        # 12 месяцев и 24 месяца: ask service_before_2022
        session.step = "vidstrochka_service_before_2022"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SERVICE_BEFORE_2022_PROMPT,
            reply_markup=text_input_keyboard(),
            parse_mode="HTML",
        )
        return "vidstrochka_service_before_2022"


async def handle_vidstrochka_service_since_2022(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle service years after 24.02.2022 answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if not text.isdigit() or int(text) < 0:
        await _invalid_number(update)
        return "vidstrochka_service_since_2022"

    session.answers["service_since_2022"] = int(text)
    session.push_history()

    # After service_since_2022, only 10 месяцев needs it
    # 10 месяцев: ask service_before_2022
    session.step = "vidstrochka_service_before_2022"
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.SERVICE_BEFORE_2022_PROMPT,
        reply_markup=text_input_keyboard(),
        parse_mode="HTML",
    )
    return "vidstrochka_service_before_2022"


async def handle_vidstrochka_service_before_2022(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle service years before 24.02.2022 answer."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if not text.isdigit() or int(text) < 0:
        await _invalid_number(update)
        return "vidstrochka_service_before_2022"

    session.answers["service_before_2022"] = int(text)
    session.push_history()

    # Calculate deferral period for KMU 768
    result_text = calculate_deferral_768_detailed(session.answers)
    return await _send_deferral_result(update, context, session, result_text)


async def handle_vidstrochka_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle result screen - can choose another contract."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip() if update.message else None

    if text == "📋 Обрати контракт":
        # Save planning mode status before clearing answers
        gate_2022_status = session.answers.get("gate_2022")
        # Clear previous answers and start over with contract selection
        session.answers.clear()
        if gate_2022_status:
            session.answers["gate_2022"] = gate_2022_status
        session.push_history()
        session.step = "vidstrochka_contract_type"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_CONTRACT_TYPE,
            reply_markup=vidstrochka_contract_type(),
            parse_mode="HTML",
        )
        return "vidstrochka_contract_type"

    if session.answers.get("has_deferral") and text == "Так":
        if session.answers.get("contract_term") == "1_year":
            info = texts.REGISTRATION_ONE_YEAR_CONTRACT
        else:
            info = texts.REGISTRATION_GENERAL
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            info,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "vidstrochka_result"

    if session.answers.get("has_deferral") and text == "Ні":
        from militarylaw_bot.bot.unified_conversation import _reset_to_menu
        return await _reset_to_menu(update, context)

    # Anything else: explain that a button is expected and show this result's buttons again
    answers = session.answers
    if answers.get("has_deferral"):
        keyboard = vidstrochka_registration_question()
    elif (
        answers.get("gate_2022") in ("before", "planning")
        or answers.get("contract_status") == "special_period"
        or answers.get("contract_extension") == "yes"
    ):
        keyboard = result_actions_with_contract()
    else:
        keyboard = result_actions()
    await _invalid_choice(update, keyboard)
    return "vidstrochka_result"
