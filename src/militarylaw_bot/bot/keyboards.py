"""Inline keyboard builders for each conversation step."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from militarylaw_bot.bot.callback_data import (
    AgeAtSigning,
    ContractTerm,
    ContractTerm768,
    ContractType,
    DischargedBefore768,
    Gate2022,
)


def _keyboard(buttons: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=data)] for label, data in buttons]
    )


def gate_2022() -> InlineKeyboardMarkup:
    return _keyboard([("Так", Gate2022.YES), ("Ні", Gate2022.NO)])


def back_to_contract_type() -> InlineKeyboardMarkup:
    return _keyboard([("Вибрати контракт", Gate2022.BACK_TO_CONTRACT)])


def contract_type() -> InlineKeyboardMarkup:
    return _keyboard(
        [
            ("Згідно Постанови КМУ №768 від 12.06.2026 р.", ContractType.KMU_768),
            ("Згідно Постанови КМУ №1538 від 11.02.2025 р.", ContractType.KMU_1538),
            ("Інший (на загальних підставах, укладений після 24.02.2022 р.)", ContractType.OTHER),
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
