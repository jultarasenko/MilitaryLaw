"""Unified conversation handler - single tree for all commands with integrated navigation."""

from __future__ import annotations

import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logger = logging.getLogger(__name__)

from militarylaw_bot.bot import handlers, texts
from militarylaw_bot.bot.global_session import CommandType, get_session
from militarylaw_bot.bot.unified_keyboards import (
    build_main_menu_keyboard,
    vidstrochka_gate_2022,
    szch_formation,
)
from militarylaw_bot.bot.command_vidstrochka import (
    handle_vidstrochka_gate_2022,
    handle_vidstrochka_contract_status,
    handle_vidstrochka_contract_extension,
    handle_vidstrochka_contract_type,
    handle_vidstrochka_contract_term_768,
    handle_vidstrochka_age_at_signing,
    handle_vidstrochka_contract_term,
    handle_vidstrochka_discharged_before_768,
    handle_vidstrochka_combat_periods,
    handle_vidstrochka_service_since_2022,
    handle_vidstrochka_service_before_2022,
    handle_vidstrochka_result,
)
from militarylaw_bot.bot.command_szch import (
    handle_szch_formation,
    handle_szch_want_return,
    handle_szch_first_time_awol,
    handle_szch_awol_date,
    handle_szch_return_type,
    handle_szch_simplified_submission,
    handle_szch_general_arrival,
    handle_szch_commander_consent,
    handle_szch_erdr,
    handle_szch_result,
)

_TEXT_INPUT = filters.TEXT & ~filters.COMMAND


async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle main menu selection - route to appropriate command."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip() if update.message else None
    logger.info(f"handle_menu_selection called: chat_id={chat_id}, text='{text}', session.step={session.step}")

    if text == "Відстрочка":
        session.push_history()
        session.current_command = CommandType.VIDSTROCHKA
        session.step = "vidstrochka_gate_2022"
        session.answers.clear()

        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_GATE_2022,
            reply_markup=vidstrochka_gate_2022(),
            parse_mode="HTML",
        )
        return "vidstrochka_gate_2022"

    elif text == "СЗЧ":
        session.push_history()
        session.current_command = CommandType.SZCH
        session.step = "szch_formation"
        session.answers.clear()

        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.SZCH_FORMATION_QUESTION,
            reply_markup=szch_formation(),
            parse_mode="HTML",
        )
        return "szch_formation"

    elif text == "Придатність":
        from militarylaw_bot.bot.command_prydatnist import handle_prydatnist
        await handle_prydatnist(update, context)
        return "menu"

    else:
        await update.message.reply_text("❌ Невпізнана команда. Виберіть один з варіантів.")
        return "menu"


async def _universal_back_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    """Universal handler for back/menu buttons - works at any level of tree."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "← Назад":
        if session.pop_history():
            step = session.step
            command = session.current_command

            if step == "menu":
                return await _reset_to_menu(update, context)

            if command == CommandType.VIDSTROCHKA:
                return await _dispatch_vidstrochka(update, context, session)
            elif command == CommandType.SZCH:
                return await _dispatch_szch(update, context, session)

        return session.step

    if text == "↑ Меню":
        return await _reset_to_menu(update, context)

    return None


async def _dispatch_vidstrochka(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session
) -> str:
    """Re-render vidstrochka step from history."""
    from militarylaw_bot.bot.unified_keyboards import (
        vidstrochka_gate_2022,
        vidstrochka_contract_status,
        vidstrochka_contract_extension,
        vidstrochka_contract_type,
        vidstrochka_contract_term_768,
        vidstrochka_age_at_signing,
        vidstrochka_contract_term,
        text_input_keyboard,
        result_actions,
    )

    chat_id = update.effective_chat.id
    step = session.step

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    if step == "vidstrochka_gate_2022":
        await update.message.reply_text(
            texts.ASK_GATE_2022,
            reply_markup=vidstrochka_gate_2022(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_contract_status":
        await update.message.reply_text(
            texts.ASK_CONTRACT_STATUS,
            reply_markup=vidstrochka_contract_status(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_contract_extension":
        await update.message.reply_text(
            texts.ASK_CONTRACT_EXTENSION,
            reply_markup=vidstrochka_contract_extension(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_contract_type":
        await update.message.reply_text(
            texts.ASK_CONTRACT_TYPE,
            reply_markup=vidstrochka_contract_type(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_contract_term_768":
        await update.message.reply_text(
            texts.ASK_CONTRACT_TERM,
            reply_markup=vidstrochka_contract_term_768(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_age_at_signing":
        await update.message.reply_text(
            texts.ASK_AGE_AT_SIGNING,
            reply_markup=vidstrochka_age_at_signing(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_contract_term":
        await update.message.reply_text(
            texts.ASK_CONTRACT_TERM,
            reply_markup=vidstrochka_contract_term(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_discharged_before_768":
        from militarylaw_bot.bot.unified_keyboards import vidstrochka_discharged_before_768
        await update.message.reply_text(
            texts.ASK_DISCHARGED_BEFORE_768,
            reply_markup=vidstrochka_discharged_before_768(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_combat_periods":
        await update.message.reply_text(
            texts.COMBAT_UNITS_PROMPT,
            reply_markup=text_input_keyboard(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_service_since_2022":
        await update.message.reply_text(
            texts.SERVICE_SINCE_2022_PROMPT,
            reply_markup=text_input_keyboard(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_service_before_2022":
        await update.message.reply_text(
            texts.SERVICE_BEFORE_2022_PROMPT,
            reply_markup=text_input_keyboard(),
            parse_mode="HTML",
        )
    elif step == "vidstrochka_result":
        # Result is a leaf node - we shouldn't return to it via back
        # Instead, show the last question again
        prev_step = session.get_previous_step()
        if prev_step and prev_step != "vidstrochka_result":
            session.step = prev_step
            return await _dispatch_vidstrochka(update, context, session)
        # Fallback - shouldn't happen
        return "vidstrochka_result"

    return step


async def _dispatch_szch(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session
) -> str:
    """Re-render SZCH step from history."""
    step = session.step

    if step == "szch_formation":
        return await handle_szch_formation(update, context)
    elif step == "szch_want_return":
        return await handle_szch_want_return(update, context)
    elif step == "szch_first_time_awol":
        return await handle_szch_first_time_awol(update, context)
    elif step == "szch_awol_date":
        return await handle_szch_awol_date(update, context)
    elif step == "szch_return_type":
        return await handle_szch_return_type(update, context)
    elif step == "szch_simplified_submission":
        return await handle_szch_simplified_submission(update, context)
    elif step == "szch_general_arrival":
        return await handle_szch_general_arrival(update, context)
    elif step == "szch_commander_consent":
        return await handle_szch_commander_consent(update, context)
    elif step == "szch_erdr":
        return await handle_szch_erdr(update, context)
    elif step == "szch_result":
        # Result is a leaf node - show last question instead
        prev_step = session.get_previous_step()
        if prev_step and prev_step != "szch_result":
            session.step = prev_step
            return await _dispatch_szch(update, context, session)
        # Fallback
        return "szch_result"

    return "menu"


async def _check_navigation_and_dispatch(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    """Check for navigation buttons and re-dispatch if needed."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    # Check navigation first
    nav_result = await _universal_back_handler(update, context)
    if nav_result is not None:
        return nav_result

    # Not navigation - handler will process normally
    return None


# Wrapper handlers that check navigation first
async def _vidstrochka_gate_2022_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_gate_2022(update, context)


async def _vidstrochka_contract_status_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_contract_status(update, context)


async def _vidstrochka_contract_extension_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_contract_extension(update, context)


async def _vidstrochka_contract_type_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_contract_type(update, context)


async def _vidstrochka_contract_term_768_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_contract_term_768(update, context)


async def _vidstrochka_age_at_signing_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_age_at_signing(update, context)


async def _vidstrochka_contract_term_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_contract_term(update, context)


async def _vidstrochka_discharged_before_768_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_discharged_before_768(update, context)


async def _vidstrochka_combat_periods_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_combat_periods(update, context)


async def _vidstrochka_service_since_2022_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_service_since_2022(update, context)


async def _vidstrochka_service_before_2022_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_service_before_2022(update, context)


async def _vidstrochka_result_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_vidstrochka_result(update, context)


# SZCH wrappers
async def _szch_formation_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_formation(update, context)


async def _szch_want_return_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_want_return(update, context)


async def _szch_first_time_awol_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_first_time_awol(update, context)


async def _szch_awol_date_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_awol_date(update, context)


async def _szch_return_type_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_return_type(update, context)


async def _szch_simplified_submission_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_simplified_submission(update, context)


async def _szch_general_arrival_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_general_arrival(update, context)


async def _szch_commander_consent_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_commander_consent(update, context)


async def _szch_erdr_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_erdr(update, context)


async def _szch_result_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_result(update, context)


async def _start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle /start command - entry point to conversation."""
    chat_id = update.effective_chat.id
    logger.info(f"_start_handler called: chat_id={chat_id}")
    await handlers.start(update, context)
    logger.info(f"_start_handler returning 'menu' state")
    return "menu"


async def _menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Wrapper for menu state handler."""
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_menu_selection(update, context)


async def _enter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Enter menu state from entry point."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    logger.info(f"Entering menu state from entry_points: chat_id={chat_id}")
    return await handle_menu_selection(update, context)


async def _reset_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Reset session and show menu (for ↑ Меню button)."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    session.reset_to_menu()

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.WELCOME,
        reply_markup=build_main_menu_keyboard(),
        parse_mode="HTML",
    )
    return "menu"


def build_unified_conversation() -> ConversationHandler:
    """Build unified single-tree conversation for all commands."""
    return ConversationHandler(
        name="unified_conversation",
        persistent=True,
        entry_points=[
            CommandHandler("start", _start_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, _enter_menu),
        ],
        states={
            # Main menu (initial state after /start)
            "menu": [
                MessageHandler(_TEXT_INPUT, _menu_wrapper),
            ],
            # Vidstrochka states (integrated in single tree)
            "vidstrochka_gate_2022": [MessageHandler(_TEXT_INPUT, _vidstrochka_gate_2022_wrapper)],
            "vidstrochka_contract_status": [MessageHandler(_TEXT_INPUT, _vidstrochka_contract_status_wrapper)],
            "vidstrochka_contract_extension": [MessageHandler(_TEXT_INPUT, _vidstrochka_contract_extension_wrapper)],
            "vidstrochka_contract_type": [MessageHandler(_TEXT_INPUT, _vidstrochka_contract_type_wrapper)],
            "vidstrochka_contract_term_768": [MessageHandler(_TEXT_INPUT, _vidstrochka_contract_term_768_wrapper)],
            "vidstrochka_age_at_signing": [MessageHandler(_TEXT_INPUT, _vidstrochka_age_at_signing_wrapper)],
            "vidstrochka_contract_term": [MessageHandler(_TEXT_INPUT, _vidstrochka_contract_term_wrapper)],
            "vidstrochka_discharged_before_768": [MessageHandler(_TEXT_INPUT, _vidstrochka_discharged_before_768_wrapper)],
            "vidstrochka_combat_periods": [MessageHandler(_TEXT_INPUT, _vidstrochka_combat_periods_wrapper)],
            "vidstrochka_service_since_2022": [MessageHandler(_TEXT_INPUT, _vidstrochka_service_since_2022_wrapper)],
            "vidstrochka_service_before_2022": [MessageHandler(_TEXT_INPUT, _vidstrochka_service_before_2022_wrapper)],
            "vidstrochka_result": [MessageHandler(_TEXT_INPUT, _vidstrochka_result_wrapper)],
            # SZCH states (integrated in single tree)
            "szch_formation": [MessageHandler(_TEXT_INPUT, _szch_formation_wrapper)],
            "szch_want_return": [MessageHandler(_TEXT_INPUT, _szch_want_return_wrapper)],
            "szch_first_time_awol": [MessageHandler(_TEXT_INPUT, _szch_first_time_awol_wrapper)],
            "szch_awol_date": [MessageHandler(_TEXT_INPUT, _szch_awol_date_wrapper)],
            "szch_return_type": [MessageHandler(_TEXT_INPUT, _szch_return_type_wrapper)],
            "szch_simplified_submission": [MessageHandler(_TEXT_INPUT, _szch_simplified_submission_wrapper)],
            "szch_general_arrival": [MessageHandler(_TEXT_INPUT, _szch_general_arrival_wrapper)],
            "szch_commander_consent": [MessageHandler(_TEXT_INPUT, _szch_commander_consent_wrapper)],
            "szch_erdr": [MessageHandler(_TEXT_INPUT, _szch_erdr_wrapper)],
            "szch_result": [MessageHandler(_TEXT_INPUT, _szch_result_wrapper)],
        },
        fallbacks=[
            CommandHandler("start", _start_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, _enter_menu),
        ],
    )
