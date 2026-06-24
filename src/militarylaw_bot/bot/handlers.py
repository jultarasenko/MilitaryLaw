"""Telegram update handlers for the /vidstrochka conversation.

Each conversation step is split into a `render_*` function (shows the
question, never touches session data) and an `on_*` function (reads the
user's answer, updates the session, advances). This split is what lets the
"↩ Назад" button work uniformly: going back just re-runs the `render_*`
for whichever step is on top of the session's history stack.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from telegram import CallbackQuery, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from militarylaw_bot.bot import keyboards, texts
from militarylaw_bot.bot.callback_data import (
    GO_BACK,
    AgeAtSigning,
    ContractTerm,
    ContractTerm768,
    ContractType,
    DischargedBefore768,
    Gate2022,
)
from militarylaw_bot.bot.session import Session, get_session, reset_session
from militarylaw_bot.bot.states import State
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

type Target = CallbackQuery | Message
type _RenderFn = Callable[[Target, Session], Awaitable[None]]


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.WELCOME)


async def begin_vidstrochka(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    reset_session(context)
    await render_gate_2022(update.message, get_session(context))
    return State.GATE_2022


# --- Render functions: show a question, never read the answer. ----------


async def render_gate_2022(target: Target, _session: Session) -> None:
    await _send(target, texts.ASK_GATE_2022, keyboards.gate_2022())


async def render_contract_type(target: Target, _session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TYPE, keyboards.contract_type())


async def render_contract_term_768(target: Target, _session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TERM, keyboards.contract_term_768())


async def render_age_at_signing(target: Target, _session: Session) -> None:
    await _send(target, texts.ASK_AGE_AT_SIGNING, keyboards.age_at_signing())


async def render_contract_term_1538(target: Target, _session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TERM, keyboards.contract_term())


async def render_contract_term_other(target: Target, _session: Session) -> None:
    await _send(target, texts.ASK_CONTRACT_TERM, keyboards.contract_term())


async def render_discharged_before_768(target: Target, _session: Session) -> None:
    await _send(target, texts.ASK_DISCHARGED_BEFORE_768, keyboards.discharged_before_768())


async def render_await_combat_units(target: Target, _session: Session) -> None:
    await _send(target, texts.COMBAT_UNITS_PROMPT, keyboards.back_only())


async def render_await_service_since_2022_years(target: Target, _session: Session) -> None:
    await _send(target, texts.SERVICE_SINCE_2022_PROMPT, keyboards.back_only())


async def render_await_service_before_2022_years(target: Target, _session: Session) -> None:
    await _send(target, texts.SERVICE_BEFORE_2022_PROMPT, keyboards.back_only())


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
}


# --- Answer handlers: read the answer, push history, advance. -----------


async def on_gate_2022(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    session = get_session(context)

    if (back_state := await _handle_back(query, session, State.GATE_2022)) is not None:
        return back_state

    if query.data == Gate2022.NO:
        await query.edit_message_text(texts.NO_2022_CONTRACT, reply_markup=keyboards.back_only())
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
        await _send_final(query, texts.with_closing_note(texts.TWELVE_MONTHS_AFTER_DISCHARGE))
        return ConversationHandler.END

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
        await _send_final(query, texts.with_closing_note(texts.TWELVE_MONTHS_AFTER_DISCHARGE))
        return ConversationHandler.END

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
        await _send_final(query, texts.with_closing_note(texts.NO_DEFERRAL))
        return ConversationHandler.END

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

    session.push(State.AWAIT_SERVICE_BEFORE_2022_YEARS)
    return await _advance_past(State.AWAIT_SERVICE_BEFORE_2022_YEARS, update.message, session)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    reset_session(context)
    await update.message.reply_text(texts.CANCELLED)
    return ConversationHandler.END


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
    remaining = _UNIT_STEPS
    if completed_state is not None:
        index = next(i for i, (state, _, _) in enumerate(_UNIT_STEPS) if state is completed_state)
        remaining = _UNIT_STEPS[index + 1 :]

    for state, render, requires in remaining:
        if requires(session.pending_result):
            await render(target, session)
            return state

    await _send_final(target, texts.with_closing_note(_format_result(session)))
    return ConversationHandler.END


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
    await _RENDER_BY_STATE[state](query, session)
    return state


async def _send(target: Target, text: str, keyboard: InlineKeyboardMarkup | None = None) -> None:
    if isinstance(target, CallbackQuery):
        await target.edit_message_text(text, reply_markup=keyboard)
    else:
        await target.reply_text(text, reply_markup=keyboard)


async def _send_final(target: Target, text: str) -> None:
    """Send a closing message — these contain `texts.CLOSING_NOTE`'s HTML links."""
    if isinstance(target, CallbackQuery):
        await target.edit_message_text(text, parse_mode=ParseMode.HTML)
    else:
        await target.reply_text(text, parse_mode=ParseMode.HTML)


def _format_result(session: Session) -> str:
    return format_breakdown(
        session.pending_result,
        combat_units=session.combat_units,
        service_since_2022_years=session.service_since_2022_years,
        service_before_2022_years=session.service_before_2022_years,
    )
