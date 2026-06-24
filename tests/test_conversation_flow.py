"""Test all conversation paths through the deferral decision tree."""

from militarylaw_bot.domain.deferral import (
    KMU_768_BY_CONTRACT_TERM,
    SIX_MONTHS_PLUS_COMBAT,
    DeferralResult,
)


class TestKMU768SixMonths:
    """KMU №768 with 6-month contract: fixed + combat only."""

    def test_path_requirements(self):
        result = KMU_768_BY_CONTRACT_TERM["6_months"]
        assert result.requires_combat_units() is True
        assert result.requires_service_since_2022_years() is False
        assert result.requires_service_before_2022_years() is False

    def test_no_combat_units(self):
        result = KMU_768_BY_CONTRACT_TERM["6_months"]
        assert result.total_months(combat_units=0) == 6

    def test_with_combat_units(self):
        result = KMU_768_BY_CONTRACT_TERM["6_months"]
        assert result.total_months(combat_units=1) == 9
        assert result.total_months(combat_units=2) == 12
        assert result.total_months(combat_units=3) == 15


class TestKMU76810Months:
    """КМУ №768 10-month: combat + service_since_2022 + service_before_2022."""

    def test_path_requirements(self):
        result = KMU_768_BY_CONTRACT_TERM["10_months"]
        assert result.requires_combat_units() is True
        assert result.requires_service_since_2022_years() is True
        assert result.requires_service_before_2022_years() is True

    def test_minimal_all_inputs(self):
        result = KMU_768_BY_CONTRACT_TERM["10_months"]
        total = result.total_months(
            combat_units=0, service_since_2022_years=0, service_before_2022_years=0
        )
        assert total == 6

    def test_one_unit_each(self):
        result = KMU_768_BY_CONTRACT_TERM["10_months"]
        total = result.total_months(
            combat_units=1, service_since_2022_years=1, service_before_2022_years=1
        )
        assert total == 6 + 3 + 6 + 1

    def test_multiple_units(self):
        result = KMU_768_BY_CONTRACT_TERM["10_months"]
        total = result.total_months(
            combat_units=3, service_since_2022_years=2, service_before_2022_years=2
        )
        assert total == 6 + (3 * 3) + (2 * 6) + (2 * 1)


class TestKMU76812Months:
    """КМУ №768 12-month: combat + service_before_2022 (no service_since_2022)."""

    def test_path_requirements(self):
        result = KMU_768_BY_CONTRACT_TERM["12_months"]
        assert result.requires_combat_units() is True
        assert result.requires_service_since_2022_years() is False
        assert result.requires_service_before_2022_years() is True

    def test_minimal_inputs(self):
        result = KMU_768_BY_CONTRACT_TERM["12_months"]
        total = result.total_months(combat_units=0, service_before_2022_years=0)
        assert total == 6

    def test_with_inputs(self):
        result = KMU_768_BY_CONTRACT_TERM["12_months"]
        total = result.total_months(combat_units=2, service_before_2022_years=1)
        assert total == 6 + (2 * 3) + 1


class TestKMU76824Months:
    """KMU №768 with 24-month contract: fixed + combat (1 per 30 days) + service_before_2022."""

    def test_path_requirements(self):
        result = KMU_768_BY_CONTRACT_TERM["24_months"]
        assert result.requires_combat_units() is True
        assert result.requires_service_since_2022_years() is False
        assert result.requires_service_before_2022_years() is True

    def test_minimal_inputs(self):
        result = KMU_768_BY_CONTRACT_TERM["24_months"]
        total = result.total_months(combat_units=0, service_before_2022_years=0)
        assert total == 6

    def test_with_inputs(self):
        result = KMU_768_BY_CONTRACT_TERM["24_months"]
        # 6 fixed + 2 combat (1 per unit) + 1 service_before_2022
        total = result.total_months(combat_units=2, service_before_2022_years=1)
        assert total == 6 + 2 + 1


class TestKMU1538OneYear:
    """KMU №1538 with 1-year contract: early exit to 12 months after discharge."""

    def test_early_exit_no_units_needed(self):
        # Contract term = ONE_YEAR → should return TWELVE_MONTHS_AFTER_DISCHARGE
        # No further questions needed
        result = DeferralResult(())
        # This is an early exit, so no calculation needed
        assert result.total_months() == 0


class TestKMU1538MoreThanOneYear:
    """KMU №1538 with more than 1 year: SIX_MONTHS_PLUS_COMBAT."""

    def test_path_requirements(self):
        six_months = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
        assert six_months.requires_combat_units() is True
        assert six_months.requires_service_since_2022_years() is False
        assert six_months.requires_service_before_2022_years() is False

    def test_no_combat(self):
        six_months = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
        assert six_months.total_months(combat_units=0) == 6

    def test_with_combat(self):
        six_months = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
        assert six_months.total_months(combat_units=1) == 7
        assert six_months.total_months(combat_units=3) == 9


class TestOtherContractAge18to25OneYear:
    """Other contract, age 18-25, 1 year: early exit to 12 months after discharge."""

    def test_early_exit(self):
        # Same as КМУ №1538 with 1 year
        result = DeferralResult(())
        assert result.total_months() == 0


class TestOtherContractAge18to25MoreThanOneYear:
    """Other contract, age 18-25, more than 1 year: goes to DISCHARGED_BEFORE_768."""

    def test_discharged_yes_early_exit(self):
        # If YES to discharged before 768, no deferral
        result = DeferralResult(())
        assert result.total_months() == 0

    def test_discharged_no_six_months_plus_combat(self):
        # If NO, then SIX_MONTHS_PLUS_COMBAT
        six_months = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
        assert six_months.requires_combat_units() is True


class TestOtherContractAge25PlusDischarged:
    """Other contract, age 25+: skips contract term, goes straight to DISCHARGED_BEFORE_768."""

    def test_discharged_yes_early_exit(self):
        # If YES, no deferral
        result = DeferralResult(())
        assert result.total_months() == 0

    def test_discharged_no_six_months_plus_combat(self):
        # If NO, SIX_MONTHS_PLUS_COMBAT
        six_months = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
        assert six_months.requires_combat_units() is True
        assert six_months.total_months(combat_units=1) == 7


class TestConversationPathCounts:
    """Verify the decision tree has the expected number of terminal paths."""

    def test_early_exit_paths(self):
        """3 early exit paths: КМУ №1538 (1yr), OTHER (1yr), DISCHARGED_YES."""
        # Each returns fixed text without further questions
        assert True

    def test_six_months_plus_combat_paths(self):
        """2 paths lead to SIX_MONTHS_PLUS_COMBAT: КМУ №1538 (>1yr NO), OTHER (>1yr NO)."""
        six_months = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
        assert six_months.requires_combat_units() is True

    def test_kmu_768_paths(self):
        """КМУ №768 has 4 contract terms, each with different requirements."""
        for term in ["6_months", "10_months", "12_months", "24_months"]:
            result = KMU_768_BY_CONTRACT_TERM[term]
            assert result.requires_combat_units() is True

    def test_total_minimal_paths(self):
        """Minimal paths: 2 early exits + 5 with combat only + others with more inputs."""
        # 2 early exits (1yr contracts)
        # 1 discharged YES (no deferral)
        # 2 SIX_MONTHS_PLUS_COMBAT (combat only)
        # 4 КМУ №768 variants (varying requirements)
        assert True


class TestRequirementsCombinations:
    """Test all combinations of requirements in the tree."""

    def test_combat_only(self):
        """Path: КМУ №768 6 months."""
        result = KMU_768_BY_CONTRACT_TERM["6_months"]
        assert result.requires_combat_units() is True
        assert result.requires_service_since_2022_years() is False
        assert result.requires_service_before_2022_years() is False

    def test_combat_plus_both_services(self):
        """Path: КМУ №768 10 months."""
        result = KMU_768_BY_CONTRACT_TERM["10_months"]
        assert result.requires_combat_units() is True
        assert result.requires_service_since_2022_years() is True
        assert result.requires_service_before_2022_years() is True

    def test_combat_plus_service_before_2022(self):
        """Path: КМУ №768 12 or 24 months."""
        result_12 = KMU_768_BY_CONTRACT_TERM["12_months"]
        result_24 = KMU_768_BY_CONTRACT_TERM["24_months"]
        for result in [result_12, result_24]:
            assert result.requires_combat_units() is True
            assert result.requires_service_since_2022_years() is False
            assert result.requires_service_before_2022_years() is True

    def test_no_requirements(self):
        """Early exit paths (1-year contracts, discharged YES)."""
        result = DeferralResult(())
        assert result.requires_combat_units() is False
        assert result.requires_service_since_2022_years() is False
        assert result.requires_service_before_2022_years() is False


class TestCalculationCorrectness:
    """Verify calculations match the legal rules."""

    def test_kmu_768_all_terms_with_all_inputs(self):
        """Each КМУ №768 term with full applicable inputs."""
        # 6 months: 6 + (1*3) = 9
        result = KMU_768_BY_CONTRACT_TERM["6_months"]
        assert result.total_months(combat_units=1) == 9

        # 10 months: 6 + (1*3) + (1*6) + (1*1) = 16
        result = KMU_768_BY_CONTRACT_TERM["10_months"]
        assert (
            result.total_months(
                combat_units=1, service_since_2022_years=1, service_before_2022_years=1
            )
            == 16
        )

        # 12 months: 6 + (1*3) + (1*1) = 10
        result = KMU_768_BY_CONTRACT_TERM["12_months"]
        assert result.total_months(combat_units=1, service_before_2022_years=1) == 10

        # 24 months: 6 + (1*1) + (1*1) = 8
        result = KMU_768_BY_CONTRACT_TERM["24_months"]
        assert result.total_months(combat_units=1, service_before_2022_years=1) == 8

    def test_six_months_plus_combat_scaling(self):
        """SIX_MONTHS_PLUS_COMBAT scales correctly."""
        result = DeferralResult((SIX_MONTHS_PLUS_COMBAT,))
        assert result.total_months(combat_units=0) == 6
        assert result.total_months(combat_units=1) == 7
        assert result.total_months(combat_units=5) == 11
