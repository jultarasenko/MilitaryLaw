"""Renders a `DeferralResult` as user-facing Ukrainian text."""

from __future__ import annotations

from militarylaw_bot.domain.deferral import DeferralResult


def format_breakdown(
    result: DeferralResult,
    *,
    combat_days: int = 0,
    service_days: int = 0,
    days_since_invasion_start: int = 0,
) -> str:
    """Render each component's contribution and the resolved total, in months."""
    lines = []
    for component in result.components:
        months = component.months_for(
            combat_days=combat_days,
            service_days=service_days,
            days_since_invasion_start=days_since_invasion_start,
        )
        lines.append(f"• {component.label} = {months} міс.")

    total = result.total_months(
        combat_days=combat_days,
        service_days=service_days,
        days_since_invasion_start=days_since_invasion_start,
    )
    breakdown = "Відстрочка складатиметься з:\n" + "\n".join(lines)
    return f"{breakdown}\n\nОрієнтовний загальний строк: {total} міс."
