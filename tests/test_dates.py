from datetime import date

import pytest

from militarylaw_bot.domain.dates import (
    DateParseError,
    Period,
    days_since_invasion_start,
    parse_periods,
    parse_single_date,
    total_days,
)


def test_parses_single_period():
    periods = parse_periods("01.03.2022-15.06.2022")
    assert periods == [Period(date(2022, 3, 1), date(2022, 6, 15))]


def test_parses_multiple_comma_separated_periods():
    periods = parse_periods("01.03.2022-15.06.2022, 01.09.2023-01.12.2023")
    assert periods == [
        Period(date(2022, 3, 1), date(2022, 6, 15)),
        Period(date(2023, 9, 1), date(2023, 12, 1)),
    ]


def test_period_days_is_inclusive():
    assert Period(date(2022, 1, 1), date(2022, 1, 1)).days == 1
    assert Period(date(2022, 1, 1), date(2022, 1, 30)).days == 30


def test_total_days_sums_all_periods():
    periods = parse_periods("01.01.2023-30.01.2023, 01.03.2023-30.03.2023")
    assert total_days(periods) == 30 + 30


def test_rejects_end_before_start():
    with pytest.raises(DateParseError, match="раніше"):
        parse_periods("15.06.2022-01.03.2022")


def test_rejects_overlapping_periods():
    with pytest.raises(DateParseError, match="перетинатися"):
        parse_periods("01.01.2023-31.01.2023, 15.01.2023-15.02.2023")


def test_accepts_future_date_as_an_expected_end_date():
    # A user who hasn't been discharged yet may enter an expected/projected
    # end date to estimate their deferral in advance.
    periods = parse_periods("01.01.2099-01.02.2099")
    assert periods == [Period(date(2099, 1, 1), date(2099, 2, 1))]


def test_rejects_implausibly_old_date():
    with pytest.raises(DateParseError, match="надто давня"):
        parse_periods("01.01.1990-01.02.1990")


def test_rejects_malformed_text():
    with pytest.raises(DateParseError):
        parse_periods("not a date")


def test_rejects_empty_input():
    with pytest.raises(DateParseError, match="жодного періоду"):
        parse_periods("")


def test_accepts_dash_variants_and_two_digit_year():
    periods = parse_periods("01.01.22–05.01.22")
    assert periods == [Period(date(2022, 1, 1), date(2022, 1, 5))]


def test_parse_single_date():
    assert parse_single_date("01.06.2023") == date(2023, 6, 1)


def test_parse_single_date_accepts_future_date():
    assert parse_single_date("01.01.2099") == date(2099, 1, 1)


def test_parse_single_date_rejects_empty_input():
    with pytest.raises(DateParseError, match="Не вказано дату"):
        parse_single_date("")


def test_days_since_invasion_start_is_inclusive_of_both_ends():
    assert days_since_invasion_start(date(2022, 2, 24)) == 1
    assert days_since_invasion_start(date(2022, 2, 25)) == 2
    assert days_since_invasion_start(date(2023, 2, 24)) == 366


def test_days_since_invasion_start_returns_zero_for_earlier_dates():
    assert days_since_invasion_start(date(2022, 1, 1)) == 0
