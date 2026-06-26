#!/usr/bin/env python3
"""Send statistics immediately."""

import asyncio
import json
import subprocess

from dotenv import load_dotenv
from telegram import Bot, constants

load_dotenv()

import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID"))


async def main():
    bot = Bot(token=BOT_TOKEN)

    # Read user count from Docker container
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "bot", "cat", "/app/data/users.json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            user_count = len(data.get("user_ids", []))
        else:
            user_count = 0
    except Exception:
        user_count = 0

    message = (
        "📊 <b>Щоденна статистика бота</b>\n\n"
        f"👥 Всього користувачів: <b>{user_count}</b>"
    )

    print(f"Sending stats to {ADMIN_CHAT_ID}: {user_count} users...")
    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=message,
        parse_mode=constants.ParseMode.HTML,
    )
    print("✅ Stats sent!")


if __name__ == "__main__":
    asyncio.run(main())
