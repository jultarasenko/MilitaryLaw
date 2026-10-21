"""One-off migration: move user IDs from the legacy users.json into statistics.db.

The JSON file is deleted only after every ID is confirmed to be in the database.

Locally:  python -m militarylaw_bot.db.migrate_users_json
Docker:   docker compose exec bot python -m militarylaw_bot.db.migrate_users_json
"""

from __future__ import annotations

import json
import sys

from militarylaw_bot.bot.utils import get_data_path
from militarylaw_bot.config import load_settings
from militarylaw_bot.db.statistics import StatisticsTracker


def main() -> int:
    json_path = get_data_path("users.json")
    if not json_path.exists():
        print(f"{json_path} not found, nothing to migrate")
        return 0

    with open(json_path) as f:
        user_ids = {int(uid) for uid in json.load(f).get("user_ids", [])}

    settings = load_settings()
    tracker = StatisticsTracker(get_data_path("statistics.db"), settings.stats_secret_key)
    added = tracker.import_users(user_ids)

    missing = [uid for uid in user_ids if not tracker.has_user(uid)]
    if missing:
        print(f"ERROR: {len(missing)} users missing after import, {json_path} kept")
        return 1

    json_path.unlink()
    print(
        f"Migrated {len(user_ids)} users ({added} new, {len(user_ids) - added} already present). "
        f"Deleted {json_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
