"""Implementation of /vidstrochka (deferral calculation) command.

This module re-exports the existing vidstrochka conversation from handlers.py
"""

from __future__ import annotations

import logging

from telegram.ext import ConversationHandler

from militarylaw_bot.bot.conversation import build_vidstrochka_conversation

logger = logging.getLogger(__name__)


def get_vidstrochka_conversation() -> ConversationHandler:
    """Get the /vidstrochka conversation handler."""
    logger.info("Building /vidstrochka conversation")
    return build_vidstrochka_conversation()
