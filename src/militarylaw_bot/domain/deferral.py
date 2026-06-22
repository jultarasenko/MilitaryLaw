"""Deferral-term calculation rules.

Encodes the decision tree from "Відстрочку на якій строк я матиму по
закінченню контракту?" (advokat Daria Tarasenko). Each `DeferralComponent`
corresponds to one lettered row (А-Д) from the source slide's reference
table; components are named A-E in code, in the same order as the slide.

This module has no Telegram dependency, so the legal rules can be unit
tested in isolation from the conversation flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class DurationBasis(Enum):
    """What user-supplied duration a component's months are computed from."""

    FIXED = auto()
    """A flat term that does not depend on any date input."""

    COMBAT_PARTICIPATION = auto()
    """Months earned per 30-day unit of direct combat participation."""

    SERVICE_SINCE_2022 = auto()
    """Months earned per full year from 24.02.2022 to the contract's signing date."""

    SERVICE_BEFORE_2022 = auto()
    """Months earned per full year of continuous service before 24.02.2022."""


@dataclass(frozen=True, slots=True)
class DeferralComponent:
    """One term that, summed with others, makes up a total deferral period."""

    label: str
    basis: DurationBasis
    fixed_months: int = 0
    months_per_unit: int = 0

    def months_for(
        self, *, combat_days: int = 0, service_days: int = 0, days_since_invasion_start: int = 0
    ) -> int:
        """Resolve this component's month contribution given user-supplied durations."""
        match self.basis:
            case DurationBasis.FIXED:
                return self.fixed_months
            case DurationBasis.COMBAT_PARTICIPATION:
                return self.fixed_months + _units_of(combat_days, 30) * self.months_per_unit
            case DurationBasis.SERVICE_SINCE_2022:
                years = _units_of(days_since_invasion_start, 365)
                return self.fixed_months + years * self.months_per_unit
            case DurationBasis.SERVICE_BEFORE_2022:
                return self.fixed_months + _units_of(service_days, 365) * self.months_per_unit


def _units_of(days: int, unit_size: int) -> int:
    return days // unit_size


# Component A — slide row А: flat 6 months, no date input required.
FIXED_BASE = DeferralComponent(
    label="фіксована частина відстрочки",
    basis=DurationBasis.FIXED,
    fixed_months=6,
)

# Component B — slide row Б: 3 months per 30 days of direct combat participation.
COMBAT_3_PER_30_DAYS = DeferralComponent(
    label="за кожні 30 днів безпосередньої участі у бойових діях, по 3 місяці",
    basis=DurationBasis.COMBAT_PARTICIPATION,
    months_per_unit=3,
)

# Component C — slide row В: 6 months per full year of service from 24.02.2022
# until the contract was signed.
SERVICE_SINCE_2022_6_PER_YEAR = DeferralComponent(
    label="за кожний рік військової служби з 24.02.2022 р. до укладення контракту, по 6 місяців",
    basis=DurationBasis.SERVICE_SINCE_2022,
    months_per_unit=6,
)

# Component D — slide row Г: 1 month per full year of continuous service
# before 24.02.2022.
SERVICE_BEFORE_2022_1_PER_YEAR = DeferralComponent(
    label="за кожний рік безперервної військової служби до 24.02.2022 р., по 1 місяцю",
    basis=DurationBasis.SERVICE_BEFORE_2022,
    months_per_unit=1,
)

# Component E — slide row Д: 1 month per 30 days of direct combat participation.
COMBAT_1_PER_30_DAYS = DeferralComponent(
    label="за кожні 30 днів безпосередньої участі у бойових діях, по 1 місяцю",
    basis=DurationBasis.COMBAT_PARTICIPATION,
    months_per_unit=1,
)

# Shared outcome for two branches of the tree: КМУ №1538 contracts signed for
# more than 1 year, and "other" post-24.02.2022 contracts (more than 1 year,
# discharged before 16.06.2026). Both resolve to "6 months base +
# 1 month per 30 days of combat participation".
SIX_MONTHS_PLUS_COMBAT = DeferralComponent(
    label="6 місяців + по 1 місяцю за кожні 30 днів безпосередньої участі у бойових діях",
    basis=DurationBasis.COMBAT_PARTICIPATION,
    fixed_months=6,
    months_per_unit=1,
)


@dataclass(frozen=True, slots=True)
class DeferralResult:
    """The resolved outcome of the decision tree for one user."""

    components: tuple[DeferralComponent, ...]

    def total_months(
        self, *, combat_days: int = 0, service_days: int = 0, days_since_invasion_start: int = 0
    ) -> int:
        return sum(
            component.months_for(
                combat_days=combat_days,
                service_days=service_days,
                days_since_invasion_start=days_since_invasion_start,
            )
            for component in self.components
        )

    def requires_combat_days(self) -> bool:
        return any(c.basis is DurationBasis.COMBAT_PARTICIPATION for c in self.components)

    def requires_signing_date(self) -> bool:
        return any(c.basis is DurationBasis.SERVICE_SINCE_2022 for c in self.components)

    def requires_service_days(self) -> bool:
        return any(c.basis is DurationBasis.SERVICE_BEFORE_2022 for c in self.components)


# КМУ №768 branch: deferral depends on the signed contract's term.
KMU_768_BY_CONTRACT_TERM: dict[str, DeferralResult] = {
    "6_months": DeferralResult((FIXED_BASE, COMBAT_3_PER_30_DAYS)),
    "10_months": DeferralResult(
        (
            FIXED_BASE,
            COMBAT_3_PER_30_DAYS,
            SERVICE_SINCE_2022_6_PER_YEAR,
            SERVICE_BEFORE_2022_1_PER_YEAR,
        )
    ),
    "12_months": DeferralResult((FIXED_BASE, COMBAT_3_PER_30_DAYS, SERVICE_BEFORE_2022_1_PER_YEAR)),
    "24_months": DeferralResult((FIXED_BASE, SERVICE_BEFORE_2022_1_PER_YEAR, COMBAT_1_PER_30_DAYS)),
}
