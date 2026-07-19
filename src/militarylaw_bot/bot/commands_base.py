"""Base classes and utilities for command handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes


class CommandHandler(ABC):
    """Base class for command handlers."""

    command_name: str
    description: str

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        """Handle command execution.

        Returns:
            State ID if command is part of conversation, None otherwise.
        """
        pass
