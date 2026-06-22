"""Telegram update handlers for the /vidstrochka conversation.

Each handler is a thin adapter: it reads the user's choice, delegates any
real decision to `militarylaw_bot.domain`, and renders the next prompt or
the final result via `militarylaw_bot.bot.texts`.
"""

from __future__ import annotations

from collections.abc import Callable

from telegram import CallbackQuery, Message, Update
from telegram.ext import ContextTypes, ConversationHandler

from militarylaw_bot.bot import keyboards, texts
from militarylaw_bot.bot.callback_data import (
    AgeAtSigning,
    ContractTerm,
    ContractTerm768,
    ContractType,
    DischargedBefore768,
    Gate2022,
)
from militarylaw_bot.bot.session import Session, get_session, reset_session
from militarylaw_bot.bot.states import State
from militarylaw_bot.domain.dates import (
    DateParseError,
    days_since_invasion_start,
    parse_periods,
    parse_single_date,
    total_days,
)
from militarylaw_bot.domain.deferral import (
    KMU_768_BY_CONTRACT_TERM,
    SIX_MONTHS_PLUS_COMBAT,
    DeferralResult,
)
from militarylaw_bot.domain.formatting import format_breakdown

_KMU_768_TERM_BY_CALLBACK = {
    ContractTerm768.MONTHS_6: "6_months",
    ContractTerm768.MONTHS_10: "10_months",
    ContractTerm768.MONTHS_12: "12_months",
    ContractTerm768.MONTHS_24: "24_months",
}


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.WELCOME)


async def begin_vidstrochka(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    reset_session(context)
    await update.message.reply_text(texts.ASK_GATE_2022, reply_markup=keyboards.gate_2022())
    return State.GATE_2022


async def on_gate_2022(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()

    if query.data == Gate2022.NO:
        await query.edit_message_text(
            texts.NO_2022_CONTRACT, reply_markup=keyboards.back_to_contract_type()
        )
        return State.GATE_2022

    # Gate2022.YES or Gate2022.BACK_TO_CONTRACT both lead to the same next step.
    await query.edit_message_text(texts.ASK_CONTRACT_TYPE, reply_markup=keyboards.contract_type())
    return State.CONTRACT_TYPE


async def on_contract_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()

    match query.data:
        case ContractType.KMU_768:
            keyboard = keyboards.contract_term_768()
            await query.edit_message_text(texts.ASK_CONTRACT_TERM, reply_markup=keyboard)
            return State.CONTRACT_TERM_768
        case ContractType.KMU_1538:
            keyboard = keyboards.contract_term()
            await query.edit_message_text(texts.ASK_CONTRACT_TERM, reply_markup=keyboard)
            return State.CONTRACT_TERM_1538
        case _:  # ContractType.OTHER
            keyboard = keyboards.age_at_signing()
            await query.edit_message_text(texts.ASK_AGE_AT_SIGNING, reply_markup=keyboard)
            return State.AGE_AT_SIGNING


async def on_contract_term_768(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()

    term = _KMU_768_TERM_BY_CALLBACK[ContractTerm768(query.data)]
    result = KMU_768_BY_CONTRACT_TERM[term]
    return await _advance_to_dates_or_finish(query, context, result)


async def on_age_at_signing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()

    if query.data == AgeAtSigning.AGE_25_PLUS:
        # For this age bracket, the contract's term doesn't change the outcome —
        # only discharge timing relative to 16.06.2026 does.
        await query.edit_message_text(
            texts.ASK_DISCHARGED_BEFORE_768, reply_markup=keyboards.discharged_before_768()
        )
        return State.DISCHARGED_BEFORE_768

    await query.edit_message_text(texts.ASK_CONTRACT_TERM, reply_markup=keyboards.contract_term())
    return State.CONTRACT_TERM_OTHER


async def on_contract_term_1538(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()

    if query.data == ContractTerm.ONE_YEAR:
        await query.edit_message_text(texts.with_closing_note(texts.TWELVE_MONTHS_AFTER_DISCHARGE))
        return ConversationHandler.END

    await query.edit_message_text(
        texts.ASK_DISCHARGED_BEFORE_768, reply_markup=keyboards.discharged_before_768()
    )
    return State.DISCHARGED_BEFORE_768


async def on_contract_term_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()

    if query.data == ContractTerm.ONE_YEAR:
        await query.edit_message_text(texts.with_closing_note(texts.TWELVE_MONTHS_AFTER_DISCHARGE))
        return ConversationHandler.END

    await query.edit_message_text(
        texts.ASK_DISCHARGED_BEFORE_768, reply_markup=keyboards.discharged_before_768()
    )
    return State.DISCHARGED_BEFORE_768


async def on_discharged_before_768(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()

    if query.data == DischargedBefore768.YES:
        await query.edit_message_text(texts.with_closing_note(texts.NO_DEFERRAL))
        return ConversationHandler.END

    six_months_plus_combat = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
    return await _advance_to_dates_or_finish(query, context, six_months_plus_combat)


async def on_signing_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    session = get_session(context)
    try:
        session.days_since_invasion_start = days_since_invasion_start(
            parse_single_date(update.message.text)
        )
    except DateParseError as error:
        retry_text = f"{error}\n\n{texts.RETRY_SUFFIX}{texts.SIGNING_DATE_PROMPT}"
        await update.message.reply_text(retry_text)
        return State.AWAIT_SIGNING_DATE

    return await _advance_past(State.AWAIT_SIGNING_DATE, update.message, session)


async def on_combat_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    session = get_session(context)
    try:
        session.combat_days = total_days(parse_periods(update.message.text))
    except DateParseError as error:
        retry_text = f"{error}\n\n{texts.RETRY_SUFFIX}{texts.COMBAT_DATES_PROMPT}"
        await update.message.reply_text(retry_text)
        return State.AWAIT_COMBAT_DATES

    return await _advance_past(State.AWAIT_COMBAT_DATES, update.message, session)


async def on_service_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    session = get_session(context)
    try:
        session.service_days = total_days(parse_periods(update.message.text))
    except DateParseError as error:
        retry_text = f"{error}\n\n{texts.RETRY_SUFFIX}{texts.SERVICE_DATES_PROMPT}"
        await update.message.reply_text(retry_text)
        return State.AWAIT_SERVICE_DATES

    return await _advance_past(State.AWAIT_SERVICE_DATES, update.message, session)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    reset_session(context)
    await update.message.reply_text(texts.CANCELLED)
    return ConversationHandler.END


# Ordered so a result needing several date inputs asks for them one at a
# time: signing date (for Component C) first, then combat participation,
# then pre-2022 continuous service.
_DATE_STEPS: tuple[tuple[State, str, Callable[[DeferralResult], bool]], ...] = (
    (State.AWAIT_SIGNING_DATE, texts.SIGNING_DATE_PROMPT, DeferralResult.requires_signing_date),
    (State.AWAIT_COMBAT_DATES, texts.COMBAT_DATES_PROMPT, DeferralResult.requires_combat_days),
    (State.AWAIT_SERVICE_DATES, texts.SERVICE_DATES_PROMPT, DeferralResult.requires_service_days),
)


async def _advance_to_dates_or_finish(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, result: DeferralResult
) -> State:
    session = get_session(context)
    session.pending_result = result
    session.combat_days = 0
    session.service_days = 0
    session.days_since_invasion_start = 0

    return await _advance_past(None, query, session)


async def _advance_past(
    completed_state: State | None, target: CallbackQuery | Message, session: Session
) -> State:
    """Ask the next still-needed date question after `completed_state`, or finish.

    `target` is whichever Telegram object the caller has on hand —
    a `CallbackQuery` (edits its message) or a `Message` (replies to it).
    """
    remaining = _DATE_STEPS
    if completed_state is not None:
        index = next(i for i, (state, _, _) in enumerate(_DATE_STEPS) if state is completed_state)
        remaining = _DATE_STEPS[index + 1 :]

    for state, prompt, requires in remaining:
        if requires(session.pending_result):
            await _send(target, prompt)
            return state

    await _send(target, texts.with_closing_note(_format_result(session)))
    return ConversationHandler.END


async def _send(target: CallbackQuery | Message, text: str) -> None:
    if isinstance(target, CallbackQuery):
        await target.edit_message_text(text)
    else:
        await target.reply_text(text)


def _format_result(session: Session) -> str:
    return format_breakdown(
        session.pending_result,
        combat_days=session.combat_days,
        service_days=session.service_days,
        days_since_invasion_start=session.days_since_invasion_start,
    )
