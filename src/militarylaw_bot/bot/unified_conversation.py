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
from militarylaw_bot.bot.handlers import track_stats
from militarylaw_bot.db.statistics import TRACKED_COMMANDS
from militarylaw_bot.bot.global_session import CommandType, get_session
from militarylaw_bot.bot.unified_keyboards import (
    VIDSTROCHKA_BUTTON,
    VIDSTROCHKA_LEGACY_BUTTONS,
    build_main_menu_keyboard,
    vidstrochka_gate_2022,
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
    handle_szch_first_time,
    handle_szch_result,
    show_szch_first_time,
    start_szch,
)
from militarylaw_bot.bot.command_transfer import (
    handle_transfer_start,
    handle_transfer_generic,
)
from militarylaw_bot.bot.command_prydatnist import (
    PRYDATNIST_STATES,
    handle_prydatnist_step,
    render_prydatnist_step,
    start_prydatnist,
)

_TEXT_INPUT = filters.TEXT & ~filters.COMMAND


async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle main menu selection - route to appropriate command."""
    try:
        chat_id = update.effective_chat.id
        session = get_session(chat_id)
        text = update.message.text.strip() if update.message else None
        logger.info(f"handle_menu_selection called: chat_id={chat_id}, text='{text}', len={len(text) if text else 0}, session.step={session.step}")
        logger.info(f"Text == 'Придатність': {text == 'Придатність'}")
    except Exception as e:
        logger.error(f"Error in handle_menu_selection start: {e}", exc_info=True)
        raise

    if text == VIDSTROCHKA_BUTTON or text in VIDSTROCHKA_LEGACY_BUTTONS:
        session.answers.clear()
        session.push_history()
        session.current_command = CommandType.VIDSTROCHKA
        session.step = "vidstrochka_gate_2022"
        track_stats(chat_id, "vidstrochka", "started")

        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            texts.ASK_GATE_2022,
            reply_markup=vidstrochka_gate_2022(),
            parse_mode="HTML",
        )
        return "vidstrochka_gate_2022"

    elif text == "СЗЧ":
        return await start_szch(update, context)

    # Переведення is temporarily hidden from the menu
    # elif text == "Переведення":
    #     session.answers.clear()
    #     session.current_command = CommandType.TRANSFER
    #     session.step = "transfer_formation"
    #     session.push_history()
    #     track_stats(chat_id, "transfer", "started")
    #
    #     await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    #     from militarylaw_bot.bot.unified_keyboards import transfer_formation
    #     await update.message.reply_text(
    #         texts.TRANSFER_FORMATION_QUESTION,
    #         reply_markup=transfer_formation(),
    #         parse_mode="HTML",
    #     )
    #     return "transfer_formation"

    elif text == "Придатність":
        return await start_prydatnist(update, context)

    else:
        logger.info(f"Unknown menu option, returning 'menu'")
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
        logger.info(f"Back button pressed: chat_id={chat_id}, current_step={session.step}, history_len={len(session.history)}")
        if session.pop_history():
            step = session.step
            command = session.current_command
            logger.info(f"After pop_history: step={step}, command={command}")

            if step == "menu":
                return await _reset_to_menu(update, context)

            if command == CommandType.VIDSTROCHKA:
                return await _dispatch_vidstrochka(update, context, session)
            elif command == CommandType.SZCH:
                return await _dispatch_szch(update, context, session)
            elif command == CommandType.TRANSFER:
                return await _dispatch_transfer(update, context, session)
            elif command == CommandType.PRYDATNIST:
                return await render_prydatnist_step(update, context, session)

        logger.info(f"No history to pop, returning current step: {session.step}")
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
    """Re-render SZCH step from history - just show the screen, don't process input."""
    # The only screen before the result is the first question
    session.step = "szch_first_time"
    return await show_szch_first_time(update, context)


async def _dispatch_transfer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session
) -> str:
    """Re-render transfer step from history - just show the screen, don't process input."""
    from militarylaw_bot.bot.unified_keyboards import (
        transfer_formation, transfer_service_type, transfer_initiative,
        transfer_graduate_year, transfer_zsu_ground, transfer_dpsu_ground,
        transfer_position_level, transfer_unit_type, transfer_current_unit_duration,
        transfer_previous_transfer_gap, transfer_rear_destination, transfer_combat_goal,
        transfer_yes_no, transfer_yes_no_unknown, transfer_family_circumstance,
        result_actions,
    )

    chat_id = update.effective_chat.id
    step = session.step

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    if step == "transfer_formation":
        await update.message.reply_text(
            texts.TRANSFER_FORMATION_QUESTION,
            reply_markup=transfer_formation(),
            parse_mode="HTML",
        )
    elif step == "transfer_service_type":
        await update.message.reply_text(
            texts.TRANSFER_SERVICE_TYPE,
            reply_markup=transfer_service_type(),
            parse_mode="HTML",
        )
    elif step == "transfer_initiative":
        await update.message.reply_text(
            texts.TRANSFER_INITIATIVE,
            reply_markup=transfer_initiative(),
            parse_mode="HTML",
        )
    elif step == "transfer_graduate_year":
        await update.message.reply_text(
            texts.TRANSFER_GRADUATE_YEAR,
            reply_markup=transfer_graduate_year(),
            parse_mode="HTML",
        )
    elif step == "transfer_zsu_ground":
        await update.message.reply_text(
            texts.TRANSFER_ZSU_GROUND,
            reply_markup=transfer_zsu_ground(),
            parse_mode="HTML",
        )
    elif step == "transfer_dpsu_ground":
        await update.message.reply_text(
            texts.TRANSFER_DPSU_GROUND,
            reply_markup=transfer_dpsu_ground(),
            parse_mode="HTML",
        )
    elif step == "transfer_position_level":
        await update.message.reply_text(
            texts.TRANSFER_POSITION_LEVEL,
            reply_markup=transfer_position_level(),
            parse_mode="HTML",
        )
    elif step == "transfer_unit_type":
        await update.message.reply_text(
            texts.TRANSFER_UNIT_TYPE,
            reply_markup=transfer_unit_type(),
            parse_mode="HTML",
        )
    elif step == "transfer_unit_type_unknown":
        await update.message.reply_text(
            texts.TRANSFER_UNIT_TYPE_UNKNOWN,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
    elif step == "transfer_current_unit_duration":
        await update.message.reply_text(
            texts.TRANSFER_CURRENT_UNIT_DURATION,
            reply_markup=transfer_current_unit_duration(),
            parse_mode="HTML",
        )
    elif step == "transfer_previous_transfer_gap":
        await update.message.reply_text(
            texts.TRANSFER_PREVIOUS_TRANSFER_GAP,
            reply_markup=transfer_previous_transfer_gap(),
            parse_mode="HTML",
        )
    elif step == "transfer_rear_destination":
        await update.message.reply_text(
            texts.TRANSFER_REAR_DESTINATION,
            reply_markup=transfer_rear_destination(),
            parse_mode="HTML",
        )
    elif step == "transfer_combat_goal":
        await update.message.reply_text(
            texts.TRANSFER_COMBAT_GOAL,
            reply_markup=transfer_combat_goal(),
            parse_mode="HTML",
        )
    elif step == "transfer_recommendation_letter":
        await update.message.reply_text(
            texts.TRANSFER_RECOMMENDATION_LETTER,
            reply_markup=transfer_yes_no(),
            parse_mode="HTML",
        )
    elif step == "transfer_medical_conclusion":
        await update.message.reply_text(
            texts.TRANSFER_MEDICAL_CONCLUSION,
            reply_markup=transfer_yes_no(),
            parse_mode="HTML",
        )
    elif step == "transfer_family_circumstance":
        await update.message.reply_text(
            texts.TRANSFER_FAMILY_CIRCUMSTANCE,
            reply_markup=transfer_family_circumstance(),
            parse_mode="HTML",
        )
    elif step == "transfer_supporting_documents":
        await update.message.reply_text(
            texts.TRANSFER_SUPPORTING_DOCUMENTS,
            reply_markup=transfer_yes_no(),
            parse_mode="HTML",
        )
    elif step == "transfer_officer_status":
        await update.message.reply_text(
            texts.TRANSFER_OFFICER_STATUS,
            reply_markup=transfer_yes_no(),
            parse_mode="HTML",
        )
    elif step == "transfer_command_approval":
        await update.message.reply_text(
            texts.TRANSFER_COMMAND_APPROVAL,
            reply_markup=transfer_yes_no(),
            parse_mode="HTML",
        )
    elif step == "transfer_command_health_obstacle":
        await update.message.reply_text(
            texts.TRANSFER_COMMAND_HEALTH_OBSTACLE,
            reply_markup=transfer_yes_no_unknown(),
            parse_mode="HTML",
        )
    elif step == "transfer_command_family_care_need":
        await update.message.reply_text(
            texts.TRANSFER_COMMAND_FAMILY_CARE_NEED,
            reply_markup=transfer_yes_no_unknown(),
            parse_mode="HTML",
        )
    elif step == "transfer_result":
        # Result is a leaf node - show last question instead
        prev_step = session.get_previous_step()
        if prev_step and prev_step != "transfer_result":
            session.step = prev_step
            return await _dispatch_transfer(update, context, session)
        return "transfer_result"

    return step


async def _check_navigation_and_dispatch(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    """Check for navigation buttons and re-dispatch if needed."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip() if update.message else ""
    logger.info(f"_check_navigation_and_dispatch: chat_id={chat_id}, text='{text}', step={session.step}")

    # Check navigation first
    nav_result = await _universal_back_handler(update, context)
    logger.info(f"_universal_back_handler returned: {nav_result}")
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
async def _szch_first_time_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_first_time(update, context)


async def _szch_result_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_szch_result(update, context)


async def _prydatnist_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    """Wrapper for all prydatnist states - check navigation first."""
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_prydatnist_step(update, context)


# Transfer wrappers
async def _transfer_wrapper(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    """Wrapper for all transfer states - check navigation first."""
    nav = await _check_navigation_and_dispatch(update, context)
    if nav is not None:
        return nav
    return await handle_transfer_generic(update, context)


async def _start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle /start command - entry point to conversation."""
    chat_id = update.effective_chat.id
    logger.info(f"_start_handler called: chat_id={chat_id}")
    await handlers.start(update, context)
    logger.info(f"_start_handler returning 'menu' state")
    return "menu"


async def _menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Wrapper for menu state handler."""
    text = update.message.text.strip() if update.message else ""
    logger.info(f"_menu_wrapper called: text='{text}'")
    nav = await _check_navigation_and_dispatch(update, context)
    logger.info(f"_menu_wrapper: nav={nav}")
    if nav is not None:
        return nav
    return await handle_menu_selection(update, context)


async def _enter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Enter menu state from entry point."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    logger.info(f"Entering menu state from entry_points: chat_id={chat_id}")
    return await _menu_wrapper(update, context)


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


def _command_of(state) -> str | None:
    """Map a conversation state like "szch_first_time" to its command, if tracked."""
    if not isinstance(state, str):
        return None
    command = state.split("_", 1)[0]
    return command if command in TRACKED_COMMANDS else None


def _track_progress(state: str | None, callback):
    """Record back presses and completions (moving onto a result screen) around a callback."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        chat_id = update.effective_chat.id
        command = _command_of(state)
        if command and update.message and (update.message.text or "").strip() == "← Назад":
            track_stats(chat_id, command, "back_button", step=state)

        new_state = await callback(update, context)

        new_command = _command_of(new_state)
        if new_command and new_state != state and new_state == f"{new_command}_result":
            track_stats(chat_id, new_command, "completion")
        return new_state
    return wrapper


def build_unified_conversation() -> ConversationHandler:
    """Build unified single-tree conversation for all commands."""
    conversation = ConversationHandler(
        name="unified_conversation",
        persistent=False,
        entry_points=[
            CommandHandler("start", _start_handler),
            CommandHandler("prydatnist", start_prydatnist),
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
            "szch_first_time": [MessageHandler(_TEXT_INPUT, _szch_first_time_wrapper)],
            "szch_result": [MessageHandler(_TEXT_INPUT, _szch_result_wrapper)],
            # Transfer states (integrated in single tree)
            "transfer_formation": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_service_type": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_initiative": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_graduate_year": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_unit_type": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_unit_type_unknown": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_current_unit_duration": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_previous_transfer_gap": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_zsu_ground": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_dpsu_ground": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_position_level": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_rear_destination": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_combat_goal": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_recommendation_letter": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_medical_conclusion": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_family_circumstance": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_supporting_documents": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_officer_status": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_command_approval": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_command_health_obstacle": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_command_family_care_need": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            "transfer_result": [MessageHandler(_TEXT_INPUT, _transfer_wrapper)],
            # Prydatnist states (integrated in single tree)
            **{
                state: [MessageHandler(_TEXT_INPUT, _prydatnist_wrapper)]
                for state in PRYDATNIST_STATES
            },
        },
        fallbacks=[
            CommandHandler("start", _start_handler),
            CommandHandler("prydatnist", start_prydatnist),
            MessageHandler(filters.TEXT & ~filters.COMMAND, _enter_menu),
        ],
    )
    for state, state_handlers in conversation.states.items():
        for handler in state_handlers:
            handler.callback = _track_progress(state, handler.callback)
    for handler in [*conversation.entry_points, *conversation.fallbacks]:
        handler.callback = _track_progress(None, handler.callback)
    return conversation
