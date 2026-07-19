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
            State.GATE_2022: [CallbackQueryHandler(handlers.on_gate_2022, pattern=r"^(?!pryd_)")],
            State.CONTRACT_STATUS: [CallbackQueryHandler(handlers.on_contract_status, pattern=r"^(?!pryd_)")],
            State.CONTRACT_EXTENSION: [CallbackQueryHandler(handlers.on_contract_extension, pattern=r"^(?!pryd_)")],
            State.CONTRACT_TYPE: [CallbackQueryHandler(handlers.on_contract_type, pattern=r"^(?!pryd_)")],
            State.CONTRACT_TERM_768: [CallbackQueryHandler(handlers.on_contract_term_768, pattern=r"^(?!pryd_)")],
            State.AGE_AT_SIGNING: [CallbackQueryHandler(handlers.on_age_at_signing, pattern=r"^(?!pryd_)")],
            State.CONTRACT_TERM_1538: [CallbackQueryHandler(handlers.on_contract_term_1538, pattern=r"^(?!pryd_)")],
            State.CONTRACT_TERM_OTHER: [CallbackQueryHandler(handlers.on_contract_term_other, pattern=r"^(?!pryd_)")],
            State.DISCHARGED_BEFORE_768: [CallbackQueryHandler(handlers.on_discharged_before_768, pattern=r"^(?!pryd_)")],
            State.AWAIT_COMBAT_UNITS: [
                CallbackQueryHandler(handlers.on_combat_units, pattern=r"^(?!pryd_)"),
                MessageHandler(_TEXT_INPUT, handlers.on_combat_units),
            ],
            State.AWAIT_SERVICE_SINCE_2022_YEARS: [
                CallbackQueryHandler(handlers.on_service_since_2022_years, pattern=r"^(?!pryd_)"),
                MessageHandler(_TEXT_INPUT, handlers.on_service_since_2022_years),
            ],
            State.AWAIT_SERVICE_BEFORE_2022_YEARS: [
                CallbackQueryHandler(handlers.on_service_before_2022_years, pattern=r"^(?!pryd_)"),
                MessageHandler(_TEXT_INPUT, handlers.on_service_before_2022_years),
            ],
            State.RESULT: [CallbackQueryHandler(handlers.on_result, pattern=r"^(?!pryd_)")],
        },
        fallbacks=[
            CommandHandler("vidstrochka", handlers.begin_vidstrochka),
        ],
    )
