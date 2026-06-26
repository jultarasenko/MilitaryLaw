"""Telegram update handlers for the /vidstrochka conversation.

Each conversation step is split into a `render_*` function (shows the
question, never touches session data) and an `on_*` function (reads the
user's answer, updates the session, advances). This split is what lets the
"↩ Назад" button work uniformly: going back just re-runs the `render_*`
for whichever step is on top of the session's history stack.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from militarylaw_bot.bot import keyboards, texts
from militarylaw_bot.bot.callback_data import (
    GO_BACK,
    START_NEW,
    AgeAtSigning,
    ContractTerm,
    ContractTerm768,
    ContractType,
    DischargedBefore768,
    Gate2022,
)
from militarylaw_bot.bot.session import (
    Session,
    get_session,
    reset_session,
    get_welcome_message_id,
    set_welcome_message_id,
)
from militarylaw_bot.bot.states import State
from militarylaw_bot.db import UserDatabase
from militarylaw_bot.domain.deferral import (
    KMU_768_BY_CONTRACT_TERM,
    SIX_MONTHS_PLUS_COMBAT,
    DeferralResult,
)
from militarylaw_bot.domain.formatting import format_breakdown
from militarylaw_bot.domain.quantities import QuantityParseError, parse_count

_KMU_768_TERM_BY_CALLBACK = {
    ContractTerm768.MONTHS_6: "6_months",
    ContractTerm768.MONTHS_10: "10_months",
    ContractTerm768.MONTHS_12: "12_months",
    ContractTerm768.MONTHS_24: "24_months",
}

# Message history limit - prevent unbounded growth in long conversations
_MESSAGE_ID_HISTORY_LIMIT = 10

# Global user database reference (set by app.py)
_user_db: UserDatabase | None = None

type Target = CallbackQuery | Message
type _RenderFn = Callable[[Target, Session], Awaitable[None]]


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
    # Clear entire chat history including saved results
    try:
        # Delete a range of message IDs (go back 100 messages from current)
        current_id = update.message.message_id
        for msg_id in range(max(1, current_id - 100), current_id):
            try:
                await update.message.get_bot().delete_message(
                    chat_id=update.message.chat_id, message_id=msg_id
                )
            except Exception:
                pass
    except Exception:
        pass

    # Clear all saved results and session
    reset_session(context)
    # Send fresh WELCOME message
    welcome_msg = await update.message.reply_text(texts.WELCOME)
    set_welcome_message_id(context, welcome_msg.message_id)


async def begin_vidstrochka(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    # Save existing saved results before resetting
    old_session = get_session(context)
    saved_ids = old_session.saved_message_ids.copy()

    # Delete all messages except WELCOME and saved results
    await _delete_messages_except_welcome(update.message, context)

    reset_session(context)
    session = get_session(context)
    # Restore saved results to new session
    session.saved_message_ids = saved_ids
    await render_gate_2022(update.message, session)
    return State.GATE_2022


# --- Render functions: show a question, never read the answer. ----------


async def render_gate_2022(target: Target, session: Session) -> None:
    await _send(target, texts.ASK_GATE_2022, keyboards.gate_2022(), session)


async def render_contract_type(target: Target, session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TYPE, keyboards.contract_type(), session)


async def render_contract_term_768(target: Target, session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TERM, keyboards.contract_term_768(), session)


async def render_age_at_signing(target: Target, session: Session) -> None:
    await _send(target, texts.ASK_AGE_AT_SIGNING, keyboards.age_at_signing(), session)


async def render_contract_term_1538(target: Target, session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TERM, keyboards.contract_term())


async def render_contract_term_other(target: Target, session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TERM, keyboards.contract_term())


async def render_discharged_before_768(target: Target, session: Session) -> None:
    await _send(target, texts.ASK_DISCHARGED_BEFORE_768, keyboards.discharged_before_768(), session)


async def render_await_combat_units(target: Target, session: Session) -> None:
    await _send(target, texts.COMBAT_UNITS_PROMPT, keyboards.back_only(), session)


async def render_await_service_since_2022_years(target: Target, session: Session) -> None:
    await _send(target, texts.SERVICE_SINCE_2022_PROMPT, keyboards.back_only(), session)


async def render_await_service_before_2022_years(target: Target, session: Session) -> None:
    await _send(target, texts.SERVICE_BEFORE_2022_PROMPT, keyboards.back_only(), session)


async def render_result(target: Target, session: Session) -> None:
    await _send_final(
        target,
        texts.with_closing_note(_format_result(session)),
        keyboards.result_actions(),
        session,
    )


_RENDER_BY_STATE: dict[State, _RenderFn] = {
    State.GATE_2022: render_gate_2022,
    State.CONTRACT_TYPE: render_contract_type,
    State.CONTRACT_TERM_768: render_contract_term_768,
    State.AGE_AT_SIGNING: render_age_at_signing,
    State.CONTRACT_TERM_1538: render_contract_term_1538,
    State.CONTRACT_TERM_OTHER: render_contract_term_other,
    State.DISCHARGED_BEFORE_768: render_discharged_before_768,
    State.AWAIT_COMBAT_UNITS: render_await_combat_units,
    State.AWAIT_SERVICE_SINCE_2022_YEARS: render_await_service_since_2022_years,
    State.AWAIT_SERVICE_BEFORE_2022_YEARS: render_await_service_before_2022_years,
    State.RESULT: render_result,
}


# --- Answer handlers: read the answer, push history, advance. -----------


async def on_gate_2022(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.GATE_2022)) is not None:
        return back_state

    if query.data == START_NEW:
        # Remove buttons from NO_2022_CONTRACT, save it, start new session
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        # Save message ID so it won't be deleted by /vidstrochka
        session.saved_message_ids.append(query.message.message_id)
        saved_ids = session.saved_message_ids.copy()
        reset_session(context)
        session = get_session(context)
        # Restore saved messages list to new session
        session.saved_message_ids = saved_ids
        await render_gate_2022(query.message, session)
        return State.GATE_2022

    if query.data == Gate2022.YES:
        session.push(State.GATE_2022)
        # Show NO_2022_CONTRACT text with save and back buttons
        keyboard = keyboards.message_with_save()
        await query.edit_message_text(
            texts.with_closing_note(texts.NO_2022_CONTRACT),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        return State.GATE_2022

    session.push(State.GATE_2022)
    await render_contract_type(query, session)
    return State.CONTRACT_TYPE


async def on_contract_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.CONTRACT_TYPE)) is not None:
        return back_state

    session.push(State.CONTRACT_TYPE)
    match query.data:
        case ContractType.KMU_768:
            await render_contract_term_768(query, session)
            return State.CONTRACT_TERM_768
        case ContractType.KMU_1538:
            await render_contract_term_1538(query, session)
            return State.CONTRACT_TERM_1538
        case _:  # ContractType.OTHER
            await render_age_at_signing(query, session)
            return State.AGE_AT_SIGNING


async def on_contract_term_768(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.CONTRACT_TERM_768)) is not None:
        return back_state

    session.push(State.CONTRACT_TERM_768)
    term = _KMU_768_TERM_BY_CALLBACK[ContractTerm768(query.data)]
    result = KMU_768_BY_CONTRACT_TERM[term]
    return await _advance_to_units_or_finish(query, session, result)


async def on_age_at_signing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.AGE_AT_SIGNING)) is not None:
        return back_state

    session.push(State.AGE_AT_SIGNING)

    if query.data == AgeAtSigning.AGE_25_PLUS:
        # For this age bracket, the contract's term doesn't change the outcome —
        # only discharge timing relative to 16.06.2026 does.
        await render_discharged_before_768(query, session)
        return State.DISCHARGED_BEFORE_768

    await render_contract_term_other(query, session)
    return State.CONTRACT_TERM_OTHER


async def on_contract_term_1538(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.CONTRACT_TERM_1538)) is not None:
        return back_state

    session.push(State.CONTRACT_TERM_1538)

    if query.data == ContractTerm.ONE_YEAR:
        session.pending_result = DeferralResult(())
        session.push(State.CONTRACT_TERM_1538)
        await query.edit_message_text(
            texts.with_closing_note(texts.TWELVE_MONTHS_AFTER_DISCHARGE),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboards.result_actions(),
        )
        return State.RESULT

    await render_discharged_before_768(query, session)
    return State.DISCHARGED_BEFORE_768


async def on_contract_term_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.CONTRACT_TERM_OTHER)) is not None:
        return back_state

    session.push(State.CONTRACT_TERM_OTHER)

    if query.data == ContractTerm.ONE_YEAR:
        session.pending_result = DeferralResult(())
        session.push(State.CONTRACT_TERM_1538)
        await query.edit_message_text(
            texts.with_closing_note(texts.TWELVE_MONTHS_AFTER_DISCHARGE),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboards.result_actions(),
        )
        return State.RESULT

    await render_discharged_before_768(query, session)
    return State.DISCHARGED_BEFORE_768


async def on_discharged_before_768(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.DISCHARGED_BEFORE_768)) is not None:
        return back_state

    session.push(State.DISCHARGED_BEFORE_768)

    if query.data == DischargedBefore768.YES:
        session.pending_result = DeferralResult(())
        session.push(State.DISCHARGED_BEFORE_768)
        await query.edit_message_text(
            texts.with_closing_note(texts.NO_DEFERRAL),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboards.result_actions(),
        )
        return State.RESULT

    six_months_plus_combat = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
    return await _advance_to_units_or_finish(query, session, six_months_plus_combat)


async def on_combat_units(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    session = get_session(context)

    if update.callback_query is not None:
        # The only button on this step is "Назад".
        back_state = await _handle_back(update.callback_query, session, State.AWAIT_COMBAT_UNITS)
        return back_state if back_state is not None else State.AWAIT_COMBAT_UNITS

    try:
        session.combat_units = parse_count(update.message.text)
    except QuantityParseError as error:
        retry_text = f"{error}\n\n{texts.RETRY_SUFFIX}{texts.COMBAT_UNITS_PROMPT}"
        await update.message.reply_text(retry_text, reply_markup=keyboards.back_only())
        return State.AWAIT_COMBAT_UNITS

    # Delete the message with user's input (old question is already handled by reply_text)
    await _delete_prev_messages(update.message, session)
    session.push(State.AWAIT_COMBAT_UNITS)
    return await _advance_past(State.AWAIT_COMBAT_UNITS, update.message, session)


async def on_service_since_2022_years(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    session = get_session(context)

    if update.callback_query is not None:
        # The only button on this step is "Назад".
        back_state = await _handle_back(
            update.callback_query, session, State.AWAIT_SERVICE_SINCE_2022_YEARS
        )
        return back_state if back_state is not None else State.AWAIT_SERVICE_SINCE_2022_YEARS

    try:
        session.service_since_2022_years = parse_count(update.message.text)
    except QuantityParseError as error:
        retry_text = f"{error}\n\n{texts.RETRY_SUFFIX}{texts.SERVICE_SINCE_2022_PROMPT}"
        await update.message.reply_text(retry_text, reply_markup=keyboards.back_only())
        return State.AWAIT_SERVICE_SINCE_2022_YEARS

    await _delete_prev_messages(update.message, session)
    session.push(State.AWAIT_SERVICE_SINCE_2022_YEARS)
    return await _advance_past(State.AWAIT_SERVICE_SINCE_2022_YEARS, update.message, session)


async def on_service_before_2022_years(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    session = get_session(context)

    if update.callback_query is not None:
        # The only button on this step is "Назад".
        back_state = await _handle_back(
            update.callback_query, session, State.AWAIT_SERVICE_BEFORE_2022_YEARS
        )
        return back_state if back_state is not None else State.AWAIT_SERVICE_BEFORE_2022_YEARS

    try:
        session.service_before_2022_years = parse_count(update.message.text)
    except QuantityParseError as error:
        retry_text = f"{error}\n\n{texts.RETRY_SUFFIX}{texts.SERVICE_BEFORE_2022_PROMPT}"
        await update.message.reply_text(retry_text, reply_markup=keyboards.back_only())
        return State.AWAIT_SERVICE_BEFORE_2022_YEARS

    await _delete_prev_messages(update.message, session)
    session.push(State.AWAIT_SERVICE_BEFORE_2022_YEARS)
    return await _advance_past(State.AWAIT_SERVICE_BEFORE_2022_YEARS, update.message, session)


async def on_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    """Handle back-button or start-new on result screen."""
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if query.data == START_NEW:
        # Remove buttons from result message (keep text), save it, start new session
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass  # Message may have already been edited
        # Save result message ID so it won't be deleted by /vidstrochka
        session.saved_message_ids.append(query.message.message_id)
        saved_ids = session.saved_message_ids.copy()
        reset_session(context)
        session = get_session(context)
        # Restore saved messages list to new session
        session.saved_message_ids = saved_ids
        await render_gate_2022(query.message, session)
        return State.GATE_2022

    back_state = await _handle_back(query, session, State.RESULT)
    return back_state if back_state is not None else State.RESULT


# --- Shared plumbing -------------------------------------------------------

# Ordered so a result needing several unit counts asks for them one at a
# time: combat-participation periods first, then full years of service
# since 24.02.2022, then full years of continuous service before it.
type _RequiresFn = Callable[[DeferralResult], bool]
type _UnitStep = tuple[State, _RenderFn, _RequiresFn]

_UNIT_STEPS: tuple[_UnitStep, ...] = (
    (State.AWAIT_COMBAT_UNITS, render_await_combat_units, DeferralResult.requires_combat_units),
    (
        State.AWAIT_SERVICE_SINCE_2022_YEARS,
        render_await_service_since_2022_years,
        DeferralResult.requires_service_since_2022_years,
    ),
    (
        State.AWAIT_SERVICE_BEFORE_2022_YEARS,
        render_await_service_before_2022_years,
        DeferralResult.requires_service_before_2022_years,
    ),
)


async def _advance_to_units_or_finish(
    query: CallbackQuery, session: Session, result: DeferralResult
) -> State:
    session.pending_result = result
    session.combat_units = 0
    session.service_since_2022_years = 0
    session.service_before_2022_years = 0

    return await _advance_past(None, query, session)


async def _advance_past(completed_state: State | None, target: Target, session: Session) -> State:
    """Ask the next still-needed unit-count question after `completed_state`, or finish."""
    if session.pending_result is None:
        # Should never happen — pending_result is set before calling _advance_past
        await target.reply_text("⚠️ Внутрішня помилка. Будь ласка, почніть спочатку.")
        return ConversationHandler.END

    remaining = _UNIT_STEPS
    if completed_state is not None:
        matching = [i for i, (state, _, _) in enumerate(_UNIT_STEPS) if state is completed_state]
        if matching:
            remaining = _UNIT_STEPS[matching[0] + 1 :]

    for state, render, requires in remaining:
        if requires(session.pending_result):
            await render(target, session)
            return state

    await render_result(target, session)
    return State.RESULT


async def _handle_back(
    query: CallbackQuery, session: Session, current_state: State
) -> State | None:
    """If `query` is a "Назад" tap, restore and render the previous step.

    Returns the `State` the conversation must move to (the caller's `on_*`
    handler must return this value as-is), or None if this wasn't a back-tap.
    PTB's ConversationHandler only re-routes the *next* update to the
    handlers registered under the returned state, so it's essential that we
    report the step we actually rendered — not `current_state` — or the next
    tap would be handled by the wrong callback.
    """
    if query.data != GO_BACK:
        return None

    previous = session.pop()
    if previous is None:
        # Nothing to go back to (shouldn't normally happen — the first
        # question has no "Назад" button) — just redraw the current step.
        await _RENDER_BY_STATE[current_state](query, session)
        return current_state

    state, snapshot = previous
    session.restore(snapshot)
    # Delete any old bot messages to prevent duplicates
    if (
        session.last_bot_message_id is not None
        and session.last_bot_message_id != query.message.message_id
    ):
        try:
            await query.get_bot().delete_message(
                chat_id=query.message.chat_id, message_id=session.last_bot_message_id
            )
        except Exception:
            pass
    await _RENDER_BY_STATE[state](query, session)
    return state


async def _safe_delete_message(chat_id: int, message_id: int, bot_instance) -> bool:
    """Safely delete a message, returning True if successful."""
    try:
        await bot_instance.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except Exception:
        return False


async def _delete_prev_messages(message: Message, session: Session) -> None:
    """Delete both bot's message (with question) and user's message (with answer)."""
    # Delete user's message (the one they just sent)
    await _safe_delete_message(message.chat_id, message.message_id, message.get_bot())

    # Delete bot's previous message (the question)
    if session.last_bot_message_id is not None:
        await _safe_delete_message(message.chat_id, session.last_bot_message_id, message.get_bot())
        session.last_bot_message_id = None


async def _delete_messages_except_welcome(
    message: Message, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Delete all messages except WELCOME and saved results."""
    try:
        current_id = message.message_id
        welcome_id = get_welcome_message_id(context)
        session = get_session(context)
        saved_ids = set(session.saved_message_ids)

        # Delete everything between welcome and current message, except saved
        if welcome_id is not None:
            # Delete messages from welcome+1 to current-1, skip saved ones
            for msg_id in range(welcome_id + 1, current_id):
                if msg_id not in saved_ids:
                    try:
                        await message.get_bot().delete_message(
                            chat_id=message.chat_id, message_id=msg_id
                        )
                    except Exception:
                        pass
    except Exception:
        pass


async def _send(
    target: Target,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
    session: Session | None = None,
) -> None:
    if isinstance(target, CallbackQuery):
        await target.edit_message_text(text, reply_markup=keyboard)
        # Keep track of previous message IDs for cleanup
        if session is not None and target.message.message_id != session.last_bot_message_id:
            if session.last_bot_message_id is not None:
                session.prev_bot_message_ids.append(session.last_bot_message_id)
            session.last_bot_message_id = target.message.message_id
            # Delete old messages (keep only current and one previous)
            while len(session.prev_bot_message_ids) > _MESSAGE_ID_HISTORY_LIMIT:
                old_id = session.prev_bot_message_ids.pop(0)
                await _safe_delete_message(target.message.chat_id, old_id, target.get_bot())
    else:
        msg = await target.reply_text(text, reply_markup=keyboard)
        # Save the bot's message ID for later deletion
        if session is not None:
            if session.last_bot_message_id is not None:
                session.prev_bot_message_ids.append(session.last_bot_message_id)
            session.last_bot_message_id = msg.message_id
            # Delete old messages (keep only current and one previous)
            while len(session.prev_bot_message_ids) > _MESSAGE_ID_HISTORY_LIMIT:
                old_id = session.prev_bot_message_ids.pop(0)
                await _safe_delete_message(target.chat_id, old_id, target.get_bot())


async def _send_final(
    target: Target,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
    session: Session | None = None,
) -> None:
    """Send a closing message — these contain `texts.CLOSING_NOTE`'s HTML links."""
    if isinstance(target, CallbackQuery):
        await target.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        msg = await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        # Save the bot's message ID for later deletion
        if session is not None:
            session.last_bot_message_id = msg.message_id


def _format_result(session: Session) -> str:
    return format_breakdown(
        session.pending_result,
        combat_units=session.combat_units,
        service_since_2022_years=session.service_since_2022_years,
        service_before_2022_years=session.service_before_2022_years,
    )
