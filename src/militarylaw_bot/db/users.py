"""User counting and statistics storage."""

from __future__ import annotations

import json
from pathlib import Path


class UserDatabase:
    """Simple JSON-based user counter."""

    def __init__(self, db_path: str | Path = "data/users.json"):
        self.db_path = Path(db_path)
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Can't create directory (e.g., in read-only filesystem), just load if exists
            pass
        self._users: set[int] = set()
        self._load()

    def _load(self) -> None:
        """Load users from JSON file."""
        if self.db_path.exists():
            try:
                with open(self.db_path) as f:
                    data = json.load(f)
                    self._users = set(int(chat_id) for chat_id in data.get("user_ids", []))
            except Exception:
                self._users = set()

    def _save(self) -> None:
        """Save users to JSON file."""
        try:
            with open(self.db_path, "w") as f:
                json.dump({"user_ids": sorted(self._users)}, f, indent=2)
        except Exception:
            pass

    def track_user(self, chat_id: int) -> None:
        """Record user interaction."""
        if chat_id not in self._users:
            self._users.add(chat_id)
            self._save()

    def get_user_count(self) -> int:
        """Get total number of unique users."""
        return len(self._users)
