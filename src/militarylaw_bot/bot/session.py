"""Typed accessor for the per-chat conversation state PTB stores in `user_data`.

`python-telegram-bot` persists `context.user_data` as a plain dict. Wrapping
it in a small dataclass-backed accessor keeps handler code free of string
keys and makes the data each handler depends on explicit.
"""

from __future__ import annotations

from dataclasses import dataclass

from telegram.ext import ContextTypes

from militarylaw_bot.domain.deferral import DeferralResult

_STORAGE_KEY = "session"


@dataclass
class Session:
    pending_result: DeferralResult | None = None
    combat_days: int = 0
    service_days: int = 0
    days_since_invasion_start: int = 0


def get_session(context: ContextTypes.DEFAULT_TYPE) -> Session:
    session = context.user_data.get(_STORAGE_KEY)
    if session is None:
        session = Session()
        context.user_data[_STORAGE_KEY] = session
    return session


def reset_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[_STORAGE_KEY] = Session()
