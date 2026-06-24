"""Parsing for user-supplied unit counts (combat periods, years of service).

Pure logic with no Telegram dependency, so it can be unit tested directly.
"""

from __future__ import annotations


class QuantityParseError(ValueError):
    """Raised when user input cannot be parsed into a valid non-negative count."""


def parse_count(text: str) -> int:
    """Parse a non-negative integer count from free-form user input."""
    text = text.strip()
    if not text:
        raise QuantityParseError("Не вказано число.")

    try:
        value = int(text)
    except ValueError as exc:
        raise QuantityParseError(
            f"Не вдалося розпізнати число: «{text}». Вкажіть ціле число."
        ) from exc

    if value < 0:
        raise QuantityParseError("Кількість не може бути від'ємною.")

    # Sanity check: combat periods max ~50 (5+ years of daily combat is unrealistic)
    # service years max 50+ is possible but warn anyway
    if value > 100:
        raise QuantityParseError("Занадто велике число. Максимум 100.")

    return value
