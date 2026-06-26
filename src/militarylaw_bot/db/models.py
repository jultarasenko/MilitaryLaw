"""Database models for user tracking and statistics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatUser:
    """Represents a unique chat/user interaction with the bot."""

    chat_id: int
    first_seen: datetime
    last_seen: datetime
    message_count: int = 1

    def to_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "message_count": self.message_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ChatUser:
        return cls(
            chat_id=data["chat_id"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            message_count=data.get("message_count", 1),
        )
