"""Parsing and validation for user-supplied date ranges.

Pure date logic with no Telegram or I/O dependency, so it can be unit
tested directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

_DATE_PATTERN = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})")
_PERIOD_SEPARATOR = re.compile(r"[,;\n]+")
_RANGE_SEPARATOR = re.compile(r"\s*[-–—]\s*")

EARLIEST_PLAUSIBLE_DATE = date(2014, 1, 1)

FULL_SCALE_INVASION_START = date(2022, 2, 24)
"""24.02.2022 — the reference date Component C and D spans are measured against."""


class DateParseError(ValueError):
    """Raised when user input cannot be parsed into a valid date range."""


@dataclass(frozen=True, slots=True)
class Period:
    """An inclusive date range, e.g. one stretch of combat participation."""

    start: date
    end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def parse_periods(text: str) -> list[Period]:
    """Parse "dd.mm.yyyy-dd.mm.yyyy, dd.mm.yyyy-dd.mm.yyyy" into `Period`s.

    Multiple periods may be separated by commas, semicolons, or newlines.
    Each period's start and end are separated by a hyphen or dash.
    Raises `DateParseError` on malformed, out-of-range, or overlapping input.
    """
    periods = [_parse_one_period(chunk) for chunk in _split_non_empty(text)]
    if not periods:
        raise DateParseError("Не вказано жодного періоду.")

    _ensure_no_overlaps(periods)
    return periods


def total_days(periods: list[Period]) -> int:
    return sum(period.days for period in periods)


def parse_single_date(text: str) -> date:
    """Parse a single "dd.mm.yyyy" date, e.g. a contract signing date."""
    chunk = text.strip()
    if not chunk:
        raise DateParseError("Не вказано дату.")
    return _parse_one_date(chunk)


def days_since_invasion_start(signing_date: date) -> int:
    """Days from 24.02.2022 (inclusive) to `signing_date` (inclusive).

    Used for Component C, whose legal span runs "from 24.02.2022 to the
    contract's signing date" rather than from a user-supplied start date.
    """
    if signing_date < FULL_SCALE_INVASION_START:
        return 0
    return (signing_date - FULL_SCALE_INVASION_START).days + 1


def _split_non_empty(text: str) -> list[str]:
    return [chunk.strip() for chunk in _PERIOD_SEPARATOR.split(text.strip()) if chunk.strip()]


def _parse_one_period(chunk: str) -> Period:
    parts = _RANGE_SEPARATOR.split(chunk)
    if len(parts) != 2:
        raise DateParseError(
            f"Не вдалося розпізнати період: «{chunk}». Очікується формат дд.мм.рррр-дд.мм.рррр"
        )

    start, end = _parse_one_date(parts[0]), _parse_one_date(parts[1])
    if end < start:
        raise DateParseError(f"Дата завершення раніше дати початку в періоді «{chunk}»")

    return Period(start, end)


def _parse_one_date(text: str) -> date:
    text = text.strip()
    match = _DATE_PATTERN.fullmatch(text)
    if not match:
        raise DateParseError(f"Не вдалося розпізнати дату: «{text}»")

    day, month, year = (int(group) for group in match.groups())
    if year < 100:
        year += 2000

    try:
        parsed = date(year, month, day)
    except ValueError as exc:
        raise DateParseError(f"Некоректна дата: «{text}»") from exc

    if parsed < EARLIEST_PLAUSIBLE_DATE:
        raise DateParseError(f"Дата «{text}» виглядає некоректною (надто давня).")

    return parsed


def _ensure_no_overlaps(periods: list[Period]) -> None:
    ordered = sorted(periods, key=lambda period: period.start)
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.start <= previous.end:
            raise DateParseError("Періоди не повинні перетинатися.")
