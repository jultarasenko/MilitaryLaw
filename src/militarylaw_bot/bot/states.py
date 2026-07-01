"""Conversation states for the /vidstrochka flow."""

from __future__ import annotations

from enum import IntEnum, auto


class State(IntEnum):
    GATE_2022 = auto()
    CONTRACT_STATUS = auto()
    CONTRACT_EXTENSION = auto()
    CONTRACT_TYPE = auto()
    CONTRACT_TERM_768 = auto()
    AGE_AT_SIGNING = auto()
    CONTRACT_TERM_1538 = auto()
    CONTRACT_TERM_OTHER = auto()
    DISCHARGED_BEFORE_768 = auto()
    AWAIT_COMBAT_UNITS = auto()
    AWAIT_SERVICE_SINCE_2022_YEARS = auto()
    AWAIT_SERVICE_BEFORE_2022_YEARS = auto()
    RESULT = auto()
