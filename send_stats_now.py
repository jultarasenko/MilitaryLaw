#!/usr/bin/env python3
"""Send statistics immediately."""

import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot

from src.militarylaw_bot.db import UserDatabase
from src.militarylaw_bot.jobs import send_daily_stats

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID"))


async def main():
    bot = Bot(token=BOT_TOKEN)
    user_db = UserDatabase()

    print(f"Sending stats to {ADMIN_CHAT_ID}...")
    await send_daily_stats(bot, ADMIN_CHAT_ID, user_db)
    print("✅ Stats sent!")


if __name__ == "__main__":
    asyncio.run(main())
