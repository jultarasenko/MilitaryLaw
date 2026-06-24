"""Renders a `DeferralResult` as user-facing Ukrainian text."""

from __future__ import annotations

from militarylaw_bot.domain.deferral import DeferralResult


def format_breakdown(
    result: DeferralResult,
    *,
    combat_units: int = 0,
    service_since_2022_years: int = 0,
    service_before_2022_years: int = 0,
) -> str:
    """Render each component's contribution and the resolved total, in months."""
    lines = []
    for component in result.components:
        months = component.months_for(
            combat_units=combat_units,
            service_since_2022_years=service_since_2022_years,
            service_before_2022_years=service_before_2022_years,
        )
        lines.append(f"• {component.label} = {months} міс.")

    total = result.total_months(
        combat_units=combat_units,
        service_since_2022_years=service_since_2022_years,
        service_before_2022_years=service_before_2022_years,
    )
    breakdown = "Відстрочка складатиметься з:\n" + "\n".join(lines)
    return f"{breakdown}\n\nОрієнтовний загальний строк: {total} міс."
