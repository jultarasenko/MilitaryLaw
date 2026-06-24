"""Callback-data constants for inline keyboard buttons.

Centralized here (instead of inline string literals scattered across
handlers) so every button's identifier is declared once and typo-proof.
"""

from __future__ import annotations

from enum import StrEnum

GO_BACK = "go_back"
"""Shared callback data for the "↩ Назад" button, present on every question."""


class Gate2022(StrEnum):
    YES = "gate_2022_yes"
    NO = "gate_2022_no"


class ContractType(StrEnum):
    KMU_768 = "contract_kmu_768"
    KMU_1538 = "contract_kmu_1538"
    OTHER = "contract_other"


class ContractTerm768(StrEnum):
    MONTHS_6 = "term768_6_months"
    MONTHS_10 = "term768_10_months"
    MONTHS_12 = "term768_12_months"
    MONTHS_24 = "term768_24_months"


class ContractTerm(StrEnum):
    """Shared by the КМУ №1538 and "other contract" branches."""

    ONE_YEAR = "term_one_year"
    MORE_THAN_ONE_YEAR = "term_more_than_one_year"


class AgeAtSigning(StrEnum):
    AGE_18_25 = "age_18_25"
    AGE_25_PLUS = "age_25_plus"


class DischargedBefore768(StrEnum):
    YES = "discharged_before_768_yes"
    NO = "discharged_before_768_no"
