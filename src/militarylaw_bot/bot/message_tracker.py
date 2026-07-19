"""Track last message for each command per user."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)


@dataclass
class MessageRecord:
    """Last message for a specific user + command."""
    user_id: int
    command: str  # "prydatnist" or "vidstrochka"
    chat_id: int
    message_id: int


class MessageTracker:
    """SQLite-based tracker for last message per user per command."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        """Create tables if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS last_messages (
                    user_id INTEGER NOT NULL,
                    command TEXT NOT NULL,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, command)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_messages (
                    user_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, message_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS helper_messages (
                    user_id INTEGER NOT NULL,
                    command TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, command)
                )
            """)
            conn.commit()

    def get_last_message(self, user_id: int, command: str) -> MessageRecord | None:
        """Get last message for user + command."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, command, chat_id, message_id FROM last_messages WHERE user_id = ? AND command = ?",
                (user_id, command)
            )
            row = cursor.fetchone()

        if not row:
            return None

        return MessageRecord(
            user_id=row[0],
            command=row[1],
            chat_id=row[2],
            message_id=row[3]
        )

    def set_last_message(self, user_id: int, command: str, chat_id: int, message_id: int) -> None:
        """Set last message for user + command."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO last_messages (user_id, command, chat_id, message_id)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, command, chat_id, message_id)
            )
            conn.commit()
        logger.info(f"📌 Stored message {message_id} for user {user_id} command {command}")

    def clear_command(self, user_id: int, command: str) -> None:
        """Clear last message for user + command."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM last_messages WHERE user_id = ? AND command = ?",
                (user_id, command)
            )
            conn.commit()

    def save_message(self, user_id: int, message_id: int) -> None:
        """Mark a message as saved (won't be deleted by /start)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO saved_messages (user_id, message_id) VALUES (?, ?)",
                (user_id, message_id)
            )
            conn.commit()
        logger.info(f"💾 Saved message {message_id} for user {user_id}")

    def is_saved(self, user_id: int, message_id: int) -> bool:
        """Check if a message is saved."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM saved_messages WHERE user_id = ? AND message_id = ?",
                (user_id, message_id)
            )
            return cursor.fetchone() is not None

    def get_saved_messages(self, user_id: int) -> list[int]:
        """Get all saved message IDs for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message_id FROM saved_messages WHERE user_id = ?",
                (user_id,)
            )
            return [row[0] for row in cursor.fetchall()]

    def set_helper_messages(self, user_id: int, command: str, message_ids: list[int]) -> None:
        """Store helper message IDs (e.g., media group with tables)."""
        # Store as comma-separated string
        ids_str = ",".join(str(mid) for mid in message_ids)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO helper_messages (user_id, command, message_id) VALUES (?, ?, ?)",
                (user_id, command, ids_str)
            )
            conn.commit()
        logger.info(f"📎 Stored {len(message_ids)} helper messages for user {user_id} command {command}")

    def get_helper_messages(self, user_id: int, command: str) -> list[int]:
        """Get all helper message IDs for user + command."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message_id FROM helper_messages WHERE user_id = ? AND command = ?",
                (user_id, command)
            )
            row = cursor.fetchone()
        if not row:
            return []
        try:
            return [int(mid) for mid in str(row[0]).split(",")]
        except (ValueError, AttributeError):
            return []

    def clear_helper_messages(self, user_id: int, command: str) -> None:
        """Clear helper messages for user + command."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM helper_messages WHERE user_id = ? AND command = ?",
                (user_id, command)
            )
            conn.commit()
