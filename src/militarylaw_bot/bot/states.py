"""Conversation states for the /vidstrochka flow."""

from __future__ import annotations

from enum import IntEnum, auto


class State(IntEnum):
    # /vidstrochka states
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

    # /prydatnist states
    SEARCH_DISEASE = auto()
    SELECT_DISEASE_FROM_KEYWORD = auto()
    SELECT_GROUP = auto()
    SELECT_ARTICLE = auto()
    SELECT_POINT = auto()
    SELECT_MILITARY_UNITS = auto()
    ASK_HEALTH_PARAMS = auto()
    FINAL_RESULT = auto()
