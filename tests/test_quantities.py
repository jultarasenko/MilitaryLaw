import pytest

from militarylaw_bot.domain.quantities import QuantityParseError, parse_count


def test_parses_zero():
    assert parse_count("0") == 0


def test_parses_positive_integer():
    assert parse_count("3") == 3


def test_strips_surrounding_whitespace():
    assert parse_count("  2  ") == 2


def test_rejects_empty_input():
    with pytest.raises(QuantityParseError, match="Не вказано число"):
        parse_count("")


def test_rejects_negative_numbers():
    with pytest.raises(QuantityParseError, match="від'ємною"):
        parse_count("-1")


def test_rejects_non_numeric_text():
    with pytest.raises(QuantityParseError, match="Не вдалося розпізнати"):
        parse_count("два")


def test_rejects_decimal_numbers():
    with pytest.raises(QuantityParseError):
        parse_count("1.5")
