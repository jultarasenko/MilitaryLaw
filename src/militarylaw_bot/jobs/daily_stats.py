"""Statistics reporting."""

from __future__ import annotations

import logging

from telegram import Bot
from telegram.constants import ParseMode

from militarylaw_bot.db import UserDatabase

logger = logging.getLogger(__name__)


async def send_stats(bot: Bot, admin_chat_id: int, user_db: UserDatabase) -> None:
    """Send current statistics to admin.

    Note: Despite the legacy module name (daily_stats.py), this function
    sends statistics on-demand via /stats command, not on a daily schedule.
    """
    try:
        user_count = user_db.get_user_count()

        message = (
            "📊 <b>Статистика бота:</b>\n\n"
            f"👥 Всього користувачів: <b>{user_count}</b>"
        )

        await bot.send_message(
            chat_id=admin_chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
        )
        logger.info(f"Stats sent to admin {admin_chat_id}: {user_count} users")
    except Exception as e:
        logger.error(f"Failed to send stats: {e}")


# Legacy alias for backward compatibility
send_daily_stats = send_stats
