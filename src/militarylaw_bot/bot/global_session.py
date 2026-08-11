"""Unified session management for all bot commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CommandType(str, Enum):
    """Available bot commands."""
    VIDSTROCHKA = "vidstrochka"
    # PRYDATNIST = "prydatnist"
    SZCH = "szch"


@dataclass
class GlobalSession:
    """Unified session state for all commands with unified conversation tree."""
    current_command: CommandType | None = None
    step: str = "menu"
    answers: dict = field(default_factory=dict)
    history: list = field(default_factory=list)

    def push_history(self) -> None:
        """Save current state to history before moving to next step."""
        self.history.append({
            "step": self.step,
            "command": self.current_command,
            "answers": dict(self.answers),
        })

    def pop_history(self) -> bool:
        """Restore previous state from history. Returns True if successful."""
        if not self.history:
            return False
        previous = self.history.pop()
        self.step = previous["step"]
        self.current_command = previous["command"]
        self.answers = previous["answers"]
        return True

    def get_previous_step(self) -> str | None:
        """Peek at previous step without popping. Returns None if no history."""
        if not self.history:
            return None
        return self.history[-1]["step"]

    def reset_to_menu(self) -> None:
        """Reset to main menu (keep session, clear command state)."""
        self.current_command = None
        self.step = "menu"
        self.answers.clear()
        self.history.clear()


# Global storage for active sessions
_active_sessions: dict[int, GlobalSession] = {}


def get_session(chat_id: int) -> GlobalSession:
    """Get or create session for chat."""
    if chat_id not in _active_sessions:
        _active_sessions[chat_id] = GlobalSession()
    return _active_sessions[chat_id]


def reset_session(chat_id: int) -> None:
    """Reset session to initial state."""
    if chat_id in _active_sessions:
        _active_sessions[chat_id].reset_to_menu()
