from militarylaw_bot.domain.deferral import (
    COMBAT_1_PER_30_DAYS,
    COMBAT_3_PER_30_DAYS,
    FIXED_BASE,
    KMU_768_BY_CONTRACT_TERM,
    SERVICE_BEFORE_2022_1_PER_YEAR,
    SERVICE_SINCE_2022_6_PER_YEAR,
    SIX_MONTHS_PLUS_COMBAT,
    DeferralResult,
)


def test_fixed_component_ignores_supplied_days():
    assert FIXED_BASE.months_for(combat_days=9999, service_days=9999) == 6


def test_combat_component_awards_months_per_30_days():
    assert COMBAT_3_PER_30_DAYS.months_for(combat_days=0) == 0
    assert COMBAT_3_PER_30_DAYS.months_for(combat_days=29) == 0
    assert COMBAT_3_PER_30_DAYS.months_for(combat_days=30) == 3
    assert COMBAT_3_PER_30_DAYS.months_for(combat_days=89) == 6
    assert COMBAT_1_PER_30_DAYS.months_for(combat_days=90) == 3


def test_service_since_2022_component_awards_months_per_full_year_of_signing_span():
    assert SERVICE_SINCE_2022_6_PER_YEAR.months_for(days_since_invasion_start=364) == 0
    assert SERVICE_SINCE_2022_6_PER_YEAR.months_for(days_since_invasion_start=365) == 6
    # Ignores the unrelated service_days/combat_days inputs.
    assert SERVICE_SINCE_2022_6_PER_YEAR.months_for(service_days=365, combat_days=30) == 0


def test_service_before_2022_component_awards_months_per_full_year_of_service_days():
    assert SERVICE_BEFORE_2022_1_PER_YEAR.months_for(service_days=365 * 2 + 1) == 2
    # Ignores the unrelated days_since_invasion_start input.
    assert SERVICE_BEFORE_2022_1_PER_YEAR.months_for(days_since_invasion_start=730) == 0


def test_six_months_plus_combat_component_combines_fixed_and_unit_parts():
    assert SIX_MONTHS_PLUS_COMBAT.months_for(combat_days=0) == 6
    assert SIX_MONTHS_PLUS_COMBAT.months_for(combat_days=30) == 7


def test_deferral_result_totals_all_components():
    result = DeferralResult((FIXED_BASE, COMBAT_3_PER_30_DAYS))
    assert result.total_months(combat_days=60) == 6 + 6


def test_deferral_result_reports_which_dates_it_needs():
    combat_only = DeferralResult((FIXED_BASE, COMBAT_3_PER_30_DAYS))
    assert combat_only.requires_combat_days() is True
    assert combat_only.requires_signing_date() is False
    assert combat_only.requires_service_days() is False

    since_2022_only = DeferralResult((SERVICE_SINCE_2022_6_PER_YEAR,))
    assert since_2022_only.requires_combat_days() is False
    assert since_2022_only.requires_signing_date() is True
    assert since_2022_only.requires_service_days() is False

    before_2022_only = DeferralResult((SERVICE_BEFORE_2022_1_PER_YEAR,))
    assert before_2022_only.requires_signing_date() is False
    assert before_2022_only.requires_service_days() is True

    fixed_only = DeferralResult((FIXED_BASE,))
    assert fixed_only.requires_combat_days() is False
    assert fixed_only.requires_signing_date() is False
    assert fixed_only.requires_service_days() is False


def test_kmu_768_six_month_contract_is_fixed_plus_combat():
    result = KMU_768_BY_CONTRACT_TERM["6_months"]
    assert result.requires_combat_days() is True
    assert result.requires_signing_date() is False
    assert result.requires_service_days() is False
    assert result.total_months(combat_days=30) == 6 + 3


def test_kmu_768_ten_month_contract_needs_combat_signing_and_service_days():
    result = KMU_768_BY_CONTRACT_TERM["10_months"]
    assert result.requires_combat_days() is True
    assert result.requires_signing_date() is True
    assert result.requires_service_days() is True
    total = result.total_months(combat_days=30, service_days=365, days_since_invasion_start=365)
    assert total == 6 + 3 + 6 + 1


def test_kmu_768_twenty_four_month_contract_uses_one_month_combat_rate():
    result = KMU_768_BY_CONTRACT_TERM["24_months"]
    assert result.total_months(combat_days=30, service_days=365) == 6 + 1 + 1
