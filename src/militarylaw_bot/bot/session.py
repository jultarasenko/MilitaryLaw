"""Typed accessor for the per-chat conversation state PTB stores in `user_data`.

`python-telegram-bot` persists `context.user_data` as a plain dict. Wrapping
it in a small dataclass-backed accessor keeps handler code free of string
keys and makes the data each handler depends on explicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from telegram.ext import ContextTypes

from militarylaw_bot.bot.states import State
from militarylaw_bot.domain.deferral import DeferralResult

_STORAGE_KEY = "session"


@dataclass
class Session:
    pending_result: DeferralResult | None = None
    combat_units: int = 0
    service_since_2022_years: int = 0
    service_before_2022_years: int = 0
    history: list[tuple[State, Session]] = field(default_factory=list, repr=False)

    def snapshot(self) -> Session:
        """A copy of this session's data, excluding its own history."""
        return replace(self, history=[])

    def push(self, state: State) -> None:
        """Record `state` (the question just asked) before moving past it."""
        self.history.append((state, self.snapshot()))

    def pop(self) -> tuple[State, Session] | None:
        """Remove and return the most recently recorded (state, data) pair, if any."""
        if not self.history:
            return None
        return self.history.pop()

    def restore(self, snapshot: Session) -> None:
        """Overwrite this session's data fields with a previously saved snapshot."""
        self.pending_result = snapshot.pending_result
        self.combat_units = snapshot.combat_units
        self.service_since_2022_years = snapshot.service_since_2022_years
        self.service_before_2022_years = snapshot.service_before_2022_years


def get_session(context: ContextTypes.DEFAULT_TYPE) -> Session:
    session = context.user_data.get(_STORAGE_KEY)
    if session is None:
        session = Session()
        context.user_data[_STORAGE_KEY] = session
    elif not hasattr(session, "history"):
        # Session objects persisted before the "Назад" feature was added
        # don't have this field yet — back-fill it rather than erroring.
        session.history = []
    return session


def reset_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[_STORAGE_KEY] = Session()
