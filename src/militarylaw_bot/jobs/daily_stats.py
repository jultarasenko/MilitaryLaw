"""Daily statistics job."""

from __future__ import annotations

import logging

from telegram import Bot
from telegram.constants import ParseMode

from militarylaw_bot.db import UserDatabase

logger = logging.getLogger(__name__)


async def send_daily_stats(bot: Bot, admin_chat_id: int, user_db: UserDatabase) -> None:
    """Send daily statistics to admin."""
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
        logger.info(f"Daily stats sent to {admin_chat_id}: {user_count} users")
    except Exception as e:
        logger.error(f"Failed to send daily stats: {e}")
