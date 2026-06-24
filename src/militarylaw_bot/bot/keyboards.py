"""Inline keyboard builders for each conversation step."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from militarylaw_bot.bot.callback_data import (
    GO_BACK,
    AgeAtSigning,
    ContractTerm,
    ContractTerm768,
    ContractType,
    DischargedBefore768,
    Gate2022,
)

BACK_BUTTON_LABEL = "↩ Назад"


def _keyboard(buttons: list[tuple[str, str]], *, with_back: bool = True) -> InlineKeyboardMarkup:
    """buttons: each item is (label, callback_data)."""
    rows = [[InlineKeyboardButton(label, callback_data=data)] for label, data in buttons]
    if with_back:
        rows.append([InlineKeyboardButton(BACK_BUTTON_LABEL, callback_data=GO_BACK)])
    return InlineKeyboardMarkup(rows)


def back_only() -> InlineKeyboardMarkup:
    """A lone "Назад" button, for text-input steps (date prompts)."""
    return InlineKeyboardMarkup([[InlineKeyboardButton(BACK_BUTTON_LABEL, callback_data=GO_BACK)]])


def gate_2022() -> InlineKeyboardMarkup:
    # First question of the flow — nothing to go back to.
    return _keyboard([("Так", Gate2022.YES), ("Ні", Gate2022.NO)], with_back=True)


def contract_type() -> InlineKeyboardMarkup:
    return _keyboard(
        [
            ("1️⃣", ContractType.KMU_768),
            ("2️⃣", ContractType.KMU_1538),
            ("3️⃣", ContractType.OTHER),
        ]
    )


def contract_term_768() -> InlineKeyboardMarkup:
    return _keyboard(
        [
            ("Від 6 міс.", ContractTerm768.MONTHS_6),
            ("10 міс.", ContractTerm768.MONTHS_10),
            ("12 міс.", ContractTerm768.MONTHS_12),
            ("24 міс.", ContractTerm768.MONTHS_24),
        ]
    )


def contract_term() -> InlineKeyboardMarkup:
    return _keyboard(
        [
            ("1 рік", ContractTerm.ONE_YEAR),
            ("Більше 1 року", ContractTerm.MORE_THAN_ONE_YEAR),
        ]
    )


def age_at_signing() -> InlineKeyboardMarkup:
    return _keyboard(
        [
            ("18-25 років", AgeAtSigning.AGE_18_25),
            ("25 років та старше", AgeAtSigning.AGE_25_PLUS),
        ]
    )


def discharged_before_768() -> InlineKeyboardMarkup:
    return _keyboard(
        [
            ("Ні", DischargedBefore768.NO),
            ("Так", DischargedBefore768.YES),
        ]
    )
