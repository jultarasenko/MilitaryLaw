"""Builds the /vidstrochka ConversationHandler from the handlers in `handlers.py`."""

from __future__ import annotations

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from militarylaw_bot.bot import handlers
from militarylaw_bot.bot.states import State

CONVERSATION_NAME = "vidstrochka_conversation"

_TEXT_INPUT = filters.TEXT & ~filters.COMMAND


def build_vidstrochka_conversation() -> ConversationHandler:
    return ConversationHandler(
        name=CONVERSATION_NAME,
        persistent=True,
        entry_points=[CommandHandler("vidstrochka", handlers.begin_vidstrochka)],
        states={
            State.GATE_2022: [CallbackQueryHandler(handlers.on_gate_2022)],
            State.CONTRACT_STATUS: [CallbackQueryHandler(handlers.on_contract_status)],
            State.CONTRACT_TYPE: [CallbackQueryHandler(handlers.on_contract_type)],
            State.CONTRACT_TERM_768: [CallbackQueryHandler(handlers.on_contract_term_768)],
            State.AGE_AT_SIGNING: [CallbackQueryHandler(handlers.on_age_at_signing)],
            State.CONTRACT_TERM_1538: [CallbackQueryHandler(handlers.on_contract_term_1538)],
            State.CONTRACT_TERM_OTHER: [CallbackQueryHandler(handlers.on_contract_term_other)],
            State.DISCHARGED_BEFORE_768: [CallbackQueryHandler(handlers.on_discharged_before_768)],
            State.AWAIT_COMBAT_UNITS: [
                CallbackQueryHandler(handlers.on_combat_units),
                MessageHandler(_TEXT_INPUT, handlers.on_combat_units),
            ],
            State.AWAIT_SERVICE_SINCE_2022_YEARS: [
                CallbackQueryHandler(handlers.on_service_since_2022_years),
                MessageHandler(_TEXT_INPUT, handlers.on_service_since_2022_years),
            ],
            State.AWAIT_SERVICE_BEFORE_2022_YEARS: [
                CallbackQueryHandler(handlers.on_service_before_2022_years),
                MessageHandler(_TEXT_INPUT, handlers.on_service_before_2022_years),
            ],
            State.RESULT: [CallbackQueryHandler(handlers.on_result)],
        },
        fallbacks=[
            CommandHandler("vidstrochka", handlers.begin_vidstrochka),
        ],
    )
