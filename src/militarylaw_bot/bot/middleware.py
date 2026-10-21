"""Middleware for bot features."""

from __future__ import annotations

from telegram import Update
from telegram.ext import BaseHandler, ContextTypes

from militarylaw_bot.db import StatisticsTracker


class UserTrackingHandler(BaseHandler):
    """Handler to track all user interactions."""

    def __init__(self, stats_tracker: StatisticsTracker):
        super().__init__(self.handle_update)
        self.stats_tracker = stats_tracker

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
        """Track user on every update."""
        chat_id = None

        if update.message and update.message.chat_id:
            chat_id = update.message.chat_id
        elif update.callback_query and update.callback_query.message:
            chat_id = update.callback_query.message.chat_id

        # Track all users
        if chat_id:
            self.stats_tracker.track_user(chat_id)
