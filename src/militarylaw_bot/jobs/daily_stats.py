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
        stats = user_db.get_stats()

        message = (
            "📊 <b>Щоденна статистика бота</b>\n\n"
            f"👥 Всього користувачів: <b>{stats['total_users']}</b>\n"
            f"🟢 Активних сьогодні: <b>{stats['active_today']}</b>\n"
            f"💬 Повідомлень сьогодні: <b>{stats['messages_today']}</b>\n"
            f"📅 Перший користувач: <b>{stats['first_user_date']}</b>"
        )

        await bot.send_message(
            chat_id=admin_chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
        )
        logger.info(f"Daily stats sent to {admin_chat_id}")
    except Exception as e:
        logger.error(f"Failed to send daily stats: {e}")
