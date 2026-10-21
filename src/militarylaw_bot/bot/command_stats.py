"""Implementation of /stats command."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from militarylaw_bot.config import load_settings
from militarylaw_bot.db import StatisticsTracker
from militarylaw_bot.db.statistics import TRACKED_COMMANDS

logger = logging.getLogger(__name__)

# Global reference (set by app.py)
_stats_tracker: StatisticsTracker | None = None


def set_stats_tracker(stats_tracker: StatisticsTracker) -> None:
    """Set the global statistics tracker reference."""
    global _stats_tracker
    _stats_tracker = stats_tracker


def _percent(part: int, whole: int) -> str:
    return f"{round(100 * part / whole)}%" if whole else "—"


def _build_summary(tracker: StatisticsTracker) -> str:
    users = tracker.get_user_summary()
    lines = [
        "<b>📊 Статистика використання</b>",
        "",
        "<b>👥 Користувачі</b>",
        f"Всього: {users['total']}",
        f"Активних за 30 днів: {users['active_30d']}",
        f"Нових: {users['new_7d']} за 7 днів · {users['new_30d']} за 30 днів",
        f"Поверталися (більше одного дня): {users['returning']}",
    ]

    started = tracker.get_commands_per_user("started")
    completed = tracker.get_commands_per_user("completion")
    table = [
        "Команд    " + "".join(f"{n:>4}" for n in started),
        "Почали    " + "".join(f"{v:>4}" for v in started.values()),
        "Завершили " + "".join(f"{v:>4}" for v in completed.values()),
    ]
    lines += [
        "",
        "<b>🧭 Скільки різних команд використали</b>",
        "<pre>" + "\n".join(table) + "</pre>",
    ]

    for cmd in TRACKED_COMMANDS:
        s = tracker.get_command_summary(cmd)
        lines += [
            "",
            f"<b>/{cmd}</b>",
            f"  Почали: {s['started_users']} · Завершили: {s['completed_users']} "
            f"({_percent(s['completed_users'], s['started_users'])})",
        ]
        if s["completed_users"]:
            avg = s["completions"] / s["completed_users"]
            lines += [
                f"  Завершень: {s['completions']} — в середньому {avg:.1f} на користувача "
                f"(макс. {s['max_completions_per_user']})",
                f"  Завершували в різні дні: {s['completed_on_several_days']}",
            ]
        lines.append(
            f"  Назад: {s['back_button_users']} користувачів, "
            f"{s['back_button_clicks']} натискань"
        )

    return "\n".join(lines)


async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - admin only usage statistics."""
    settings = load_settings()
    logger.info(f"User {update.message.chat_id} requested /stats")

    # Check if user is admin
    if update.message.chat_id not in settings.admin_chat_ids:
        logger.warning(f"Non-admin {update.message.chat_id} tried to access /stats")
        await update.message.reply_text("⛔ Ця команда доступна тільки адміністратору")
        return

    if _stats_tracker is None:
        await update.message.reply_text("⚠️ Статистика недоступна")
        return

    logger.info(f"Sending stats to admin {update.message.chat_id}")
    await update.message.reply_text(_build_summary(_stats_tracker), parse_mode=ParseMode.HTML)
