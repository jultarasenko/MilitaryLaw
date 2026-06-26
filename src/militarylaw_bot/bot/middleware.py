"""Middleware for bot features."""

from __future__ import annotations

from telegram import Update
from telegram.ext import BaseHandler, ContextTypes

from militarylaw_bot.db import UserDatabase


class UserTrackingHandler(BaseHandler):
    """Handler to track all user interactions."""

    def __init__(self, user_db: UserDatabase):
        super().__init__()
        self.user_db = user_db

    def check_update(self, update: object) -> bool:
        """Always process every update."""
        return isinstance(update, Update)

    async def handle_update(
        self,
        update: Update,
        application,
        check_result,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Track user on every update (except admin)."""
        from militarylaw_bot.config import load_settings

        settings = load_settings()
        chat_id = None

        if update.message and update.message.chat_id:
            chat_id = update.message.chat_id
        elif update.callback_query and update.callback_query.message:
            chat_id = update.callback_query.message.chat_id

        # Track all users except admin
        if chat_id and chat_id != settings.admin_chat_id:
            self.user_db.track_user(chat_id)
