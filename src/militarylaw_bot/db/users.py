"""User tracking and statistics storage."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from militarylaw_bot.db.models import ChatUser


class UserDatabase:
    """Simple JSON-based user database."""

    def __init__(self, db_path: str | Path = "data/users.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._users: dict[int, ChatUser] = {}
        self._load()

    def _load(self) -> None:
        """Load users from JSON file."""
        if self.db_path.exists():
            try:
                with open(self.db_path) as f:
                    data = json.load(f)
                    self._users = {int(k): ChatUser.from_dict(v) for k, v in data.items()}
            except Exception:
                self._users = {}

    def _save(self) -> None:
        """Save users to JSON file."""
        try:
            with open(self.db_path, "w") as f:
                data = {str(k): v.to_dict() for k, v in self._users.items()}
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def track_user(self, chat_id: int) -> ChatUser:
        """Record or update user interaction."""
        now = datetime.now()
        if chat_id in self._users:
            user = self._users[chat_id]
            user.last_seen = now
            user.message_count += 1
        else:
            user = ChatUser(
                chat_id=chat_id,
                first_seen=now,
                last_seen=now,
                message_count=1,
            )
            self._users[chat_id] = user

        self._save()
        return user

    def get_stats(self) -> dict:
        """Get current statistics."""
        if not self._users:
            return {
                "total_users": 0,
                "messages_today": 0,
                "active_today": 0,
                "first_user_date": None,
            }

        now = datetime.now()
        today_date = now.date()

        messages_today = sum(
            1 for user in self._users.values() if user.last_seen.date() == today_date
        )

        active_today = sum(
            1 for user in self._users.values() if user.last_seen.date() == today_date
        )

        first_user = min(self._users.values(), key=lambda u: u.first_seen)

        return {
            "total_users": len(self._users),
            "messages_today": messages_today,
            "active_today": active_today,
            "first_user_date": first_user.first_seen.strftime("%Y-%m-%d %H:%M"),
        }

    def get_all_chat_ids(self) -> list[int]:
        """Get all tracked chat IDs."""
        return list(self._users.keys())
