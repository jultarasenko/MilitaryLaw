"""Unified message tracking and cleanup for all bot commands."""

from __future__ import annotations

import logging
from typing import Optional

from telegram import CallbackQuery, Message
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Session keys for tracking messages by command
MESSAGE_TRACKING_KEY = "message_tracking"


async def track_message(
    message: Message,
    command_name: str,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Track a message and delete previous message from the same command.

    Args:
        message: The message to track
        command_name: The command this message belongs to (e.g., "prydatnist", "vidstrochka")
        context: The context for accessing user data
    """
    if not message:
        return

    chat_id = message.chat_id
    msg_id = message.message_id

    # Initialize tracking dict if needed
    if MESSAGE_TRACKING_KEY not in context.user_data:
        context.user_data[MESSAGE_TRACKING_KEY] = {}

    tracking = context.user_data[MESSAGE_TRACKING_KEY]

    # Initialize command tracking if needed
    if command_name not in tracking:
        tracking[command_name] = {"message_id": None, "chat_id": None}

    cmd_tracking = tracking[command_name]

    # Delete previous message from this command if it exists
    if cmd_tracking["message_id"] is not None and cmd_tracking["chat_id"] is not None:
        try:
            await context.bot.delete_message(
                chat_id=cmd_tracking["chat_id"],
                message_id=cmd_tracking["message_id"]
            )
            logger.info(f"🗑 Deleted previous {command_name} message {cmd_tracking['message_id']}")
        except Exception as e:
            logger.debug(f"Could not delete previous {command_name} message: {e}")

    # Track new message
    cmd_tracking["message_id"] = msg_id
    cmd_tracking["chat_id"] = chat_id
    logger.info(f"📌 Tracking {command_name} message {msg_id}")


async def track_callback_message(
    query: CallbackQuery,
    command_name: str,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Track a message from a callback and delete previous message from the same command.

    Args:
        query: The callback query containing the message
        command_name: The command this message belongs to (e.g., "prydatnist", "vidstrochka")
        context: The context for accessing user data
    """
    if not query.message:
        return

    await track_message(query.message, command_name, context)
