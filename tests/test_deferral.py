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


def test_fixed_component_ignores_supplied_units():
    assert (
        FIXED_BASE.months_for(
            combat_units=9999, service_since_2022_years=9999, service_before_2022_years=9999
        )
        == 6
    )


def test_combat_component_awards_months_per_unit():
    assert COMBAT_3_PER_30_DAYS.months_for(combat_units=0) == 0
    assert COMBAT_3_PER_30_DAYS.months_for(combat_units=1) == 3
    assert COMBAT_3_PER_30_DAYS.months_for(combat_units=2) == 6
    assert COMBAT_1_PER_30_DAYS.months_for(combat_units=3) == 3


def test_service_since_2022_component_awards_months_per_year():
    assert SERVICE_SINCE_2022_6_PER_YEAR.months_for(service_since_2022_years=0) == 0
    assert SERVICE_SINCE_2022_6_PER_YEAR.months_for(service_since_2022_years=1) == 6
    # Ignores the unrelated combat_units/service_before_2022_years inputs.
    assert (
        SERVICE_SINCE_2022_6_PER_YEAR.months_for(combat_units=5, service_before_2022_years=5) == 0
    )


def test_service_before_2022_component_awards_months_per_year():
    assert SERVICE_BEFORE_2022_1_PER_YEAR.months_for(service_before_2022_years=2) == 2
    # Ignores the unrelated combat_units/service_since_2022_years inputs.
    assert (
        SERVICE_BEFORE_2022_1_PER_YEAR.months_for(combat_units=5, service_since_2022_years=5) == 0
    )


def test_six_months_plus_combat_component_combines_fixed_and_unit_parts():
    assert SIX_MONTHS_PLUS_COMBAT.months_for(combat_units=0) == 6
    assert SIX_MONTHS_PLUS_COMBAT.months_for(combat_units=1) == 7


def test_deferral_result_totals_all_components():
    result = DeferralResult((FIXED_BASE, COMBAT_3_PER_30_DAYS))
    assert result.total_months(combat_units=2) == 6 + 6


def test_deferral_result_reports_which_inputs_it_needs():
    combat_only = DeferralResult((FIXED_BASE, COMBAT_3_PER_30_DAYS))
    assert combat_only.requires_combat_units() is True
    assert combat_only.requires_service_since_2022_years() is False
    assert combat_only.requires_service_before_2022_years() is False

    since_2022_only = DeferralResult((SERVICE_SINCE_2022_6_PER_YEAR,))
    assert since_2022_only.requires_combat_units() is False
    assert since_2022_only.requires_service_since_2022_years() is True
    assert since_2022_only.requires_service_before_2022_years() is False

    before_2022_only = DeferralResult((SERVICE_BEFORE_2022_1_PER_YEAR,))
    assert before_2022_only.requires_service_since_2022_years() is False
    assert before_2022_only.requires_service_before_2022_years() is True

    fixed_only = DeferralResult((FIXED_BASE,))
    assert fixed_only.requires_combat_units() is False
    assert fixed_only.requires_service_since_2022_years() is False
    assert fixed_only.requires_service_before_2022_years() is False


def test_kmu_768_six_month_contract_is_fixed_plus_combat():
    result = KMU_768_BY_CONTRACT_TERM["6_months"]
    assert result.requires_combat_units() is True
    assert result.requires_service_since_2022_years() is False
    assert result.requires_service_before_2022_years() is False
    assert result.total_months(combat_units=1) == 6 + 3


def test_kmu_768_ten_month_contract_needs_all_three_inputs():
    result = KMU_768_BY_CONTRACT_TERM["10_months"]
    assert result.requires_combat_units() is True
    assert result.requires_service_since_2022_years() is True
    assert result.requires_service_before_2022_years() is True
    total = result.total_months(
        combat_units=1, service_since_2022_years=1, service_before_2022_years=1
    )
    assert total == 6 + 3 + 6 + 1


def test_kmu_768_twenty_four_month_contract_uses_one_month_combat_rate():
    result = KMU_768_BY_CONTRACT_TERM["24_months"]
    total = result.total_months(combat_units=1, service_before_2022_years=1)
    assert total == 6 + 1 + 1
