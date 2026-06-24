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
_WELCOME_MSG_KEY = "welcome_message_id"


@dataclass
class Session:
    pending_result: DeferralResult | None = None
    combat_units: int = 0
    service_since_2022_years: int = 0
    service_before_2022_years: int = 0
    last_bot_message_id: int | None = None
    prev_bot_message_ids: list[int] = field(default_factory=list, repr=False)
    history: list[tuple[State, Session]] = field(default_factory=list, repr=False)
    saved_message_ids: list[int] = field(default_factory=list, repr=False)

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
        self.last_bot_message_id = snapshot.last_bot_message_id


def get_session(context: ContextTypes.DEFAULT_TYPE) -> Session:
    session = context.user_data.get(_STORAGE_KEY)
    if session is None:
        session = Session()
        context.user_data[_STORAGE_KEY] = session
    else:
        # Migrate old sessions (before unit-count model)
        if not hasattr(session, "history"):
            session.history = []
        if not hasattr(session, "combat_units"):
            session.combat_units = 0
        if not hasattr(session, "service_since_2022_years"):
            session.service_since_2022_years = 0
        if not hasattr(session, "service_before_2022_years"):
            session.service_before_2022_years = 0
        if not hasattr(session, "last_bot_message_id"):
            session.last_bot_message_id = None
        if not hasattr(session, "prev_bot_message_ids"):
            session.prev_bot_message_ids = []
        if not hasattr(session, "saved_message_ids"):
            session.saved_message_ids = []
    return session


def reset_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    # Reset session but preserve WELCOME message ID
    welcome_id = context.user_data.get(_WELCOME_MSG_KEY)
    session = Session()
    # Explicitly clear history and message IDs to prevent unbounded growth
    session.history.clear()
    session.prev_bot_message_ids.clear()
    context.user_data[_STORAGE_KEY] = session
    if welcome_id is not None:
        context.user_data[_WELCOME_MSG_KEY] = welcome_id


def get_welcome_message_id(context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Get the stored WELCOME message ID."""
    return context.user_data.get(_WELCOME_MSG_KEY)


def set_welcome_message_id(context: ContextTypes.DEFAULT_TYPE, message_id: int) -> None:
    """Store the WELCOME message ID."""
    context.user_data[_WELCOME_MSG_KEY] = message_id
