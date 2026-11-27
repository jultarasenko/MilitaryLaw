"""Usage statistics storage with pseudonymised user IDs."""

from __future__ import annotations

import hashlib
import hmac
import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# "transfer" is left out while Переведення is hidden from the menu
TRACKED_COMMANDS = ("vidstrochka", "szch", "prydatnist")


def _days_ago(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


class StatisticsTracker:
    """SQLite event log keyed by HMAC-SHA256 of the user ID.

    The same user always maps to the same hash, so distinct-user counts work,
    but the real chat ID cannot be recovered without the secret key.
    Only navigation is recorded (starts, back presses, completions), never answers.
    """

    def __init__(self, db_path: str | Path, secret_key: str):
        self.db_path = str(db_path)
        self._key = secret_key.encode()
        self._init_db()

    def _hash_user_id(self, user_id: int) -> str:
        return hmac.new(self._key, str(user_id).encode(), hashlib.sha256).hexdigest()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            # first_seen/last_seen are NULL for users imported from the legacy users.json
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_hash TEXT PRIMARY KEY,
                    first_seen TEXT,
                    last_seen TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stat_events (
                    user_hash TEXT NOT NULL,
                    command TEXT NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    step TEXT
                )
            """)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(stat_events)")}
            if "step" not in columns:
                conn.execute("ALTER TABLE stat_events ADD COLUMN step TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_stat_events_user ON stat_events(user_hash)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_stat_events_command ON stat_events(command, action)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_stat_events_created ON stat_events(created_at)"
            )
            conn.commit()

    # --- recording ---

    def track_user(self, user_id: int) -> None:
        """Record that a user interacted with the bot in any way."""
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO users (user_hash, first_seen, last_seen) VALUES (?, ?, ?) "
                "ON CONFLICT(user_hash) DO UPDATE SET last_seen = excluded.last_seen",
                (self._hash_user_id(user_id), now, now),
            )
            conn.commit()

    def import_users(self, user_ids: set[int]) -> int:
        """Add users with unknown activity dates; returns how many were new."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.executemany(
                "INSERT OR IGNORE INTO users (user_hash) VALUES (?)",
                [(self._hash_user_id(uid),) for uid in user_ids],
            )
            conn.commit()
        return cursor.rowcount

    def has_user(self, user_id: int) -> bool:
        return bool(
            self._scalar(
                "SELECT COUNT(*) FROM users WHERE user_hash = ?", (self._hash_user_id(user_id),)
            )
        )

    def track_action(
        self, user_id: int, command: str, action: str, step: str | None = None
    ) -> None:
        """Record one event: "started", "back_button" (with step) or "completion"."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO stat_events (user_hash, command, action, created_at, step) "
                "VALUES (?, ?, ?, ?, ?)",
                (self._hash_user_id(user_id), command, action, datetime.now(UTC).isoformat(), step),
            )
            conn.commit()

    # --- reporting ---

    def _scalar(self, query: str, params: tuple = ()) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(query, params).fetchone()
        return (row[0] or 0) if row else 0

    def get_user_summary(self) -> dict:
        return {
            "total": self._scalar("SELECT COUNT(*) FROM users"),
            "active_30d": self._scalar(
                "SELECT COUNT(*) FROM users WHERE last_seen >= ?", (_days_ago(30),)
            ),
            "new_7d": self._scalar(
                "SELECT COUNT(*) FROM users WHERE first_seen >= ?", (_days_ago(7),)
            ),
            "new_30d": self._scalar(
                "SELECT COUNT(*) FROM users WHERE first_seen >= ?", (_days_ago(30),)
            ),
            # Seen on more than one day; imported users count once they come back
            "returning": self._scalar(
                "SELECT COUNT(*) FROM users WHERE last_seen IS NOT NULL AND "
                "(first_seen IS NULL OR substr(last_seen, 1, 10) > substr(first_seen, 1, 10))"
            ),
        }

    def get_commands_per_user(self, action: str) -> dict[int, int]:
        """How many users did action ("started"/"completion") in exactly N different commands."""
        placeholders = ", ".join("?" for _ in TRACKED_COMMANDS)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT n, COUNT(*) FROM ("
                "  SELECT COUNT(DISTINCT command) AS n FROM stat_events"
                f"  WHERE action = ? AND command IN ({placeholders}) GROUP BY user_hash"
                ") GROUP BY n",
                (action, *TRACKED_COMMANDS),
            ).fetchall()
        counts = dict(rows)
        return {n: counts.get(n, 0) for n in range(1, len(TRACKED_COMMANDS) + 1)}

    def get_command_summary(self, command: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            started, back_users, back_clicks = conn.execute(
                "SELECT COUNT(DISTINCT CASE WHEN action = 'started' THEN user_hash END), "
                "COUNT(DISTINCT CASE WHEN action = 'back_button' THEN user_hash END), "
                "COALESCE(SUM(action = 'back_button'), 0) "
                "FROM stat_events WHERE command = ?",
                (command,),
            ).fetchone()
            completed_users, completions, max_per_user, returned = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(n), 0), COALESCE(MAX(n), 0), "
                "COALESCE(SUM(days > 1), 0) FROM ("
                "  SELECT COUNT(*) AS n, COUNT(DISTINCT substr(created_at, 1, 10)) AS days"
                "  FROM stat_events WHERE command = ? AND action = 'completion'"
                "  GROUP BY user_hash)",
                (command,),
            ).fetchone()
        return {
            "started_users": started,
            "completed_users": completed_users,
            "completions": completions,
            "max_completions_per_user": max_per_user,
            "completed_on_several_days": returned,
            "back_button_users": back_users,
            "back_button_clicks": back_clicks,
        }