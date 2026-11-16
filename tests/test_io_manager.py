"""Tests for IoManager: checking what the user types before it reaches the AI.

Run from the project root:  python -m pytest tests/test_io_manager.py -v
"""

import pytest

from managers.io_manager import IoManager


@pytest.mark.parametrize(
    "phone_number, expected_local, expected_code",
    [
        ("+6591234567", "91234567", "+65"),        # Singapore
        ("+14155550123", "4155550123", "+1"),      # US
        ("+447911123456", "7911123456", "+44"),    # UK
        ("+60123456789", "123456789", "+60"),      # Malaysia
        ("+85291234567", "91234567", "+852"),      # Hong Kong (3-digit code)
        ("6591234567", "91234567", "+65"),         # "+" added automatically
        ("+65 9123 4567", "91234567", "+65"),      # spaces allowed
    ],
)
def test_split_number_into_local_number_and_country_code(phone_number, expected_local, expected_code):
    assert IoManager().split_number(phone_number) == (expected_local, expected_code)


@pytest.mark.parametrize(
    "phone_number",
    [
        "abc",          # not a number
        "",             # empty
        "91234567",     # no country code: read as +91..., not a valid number
        "+6512",        # too short
    ],
)
def test_invalid_phone_number_raises_value_error(phone_number):
    with pytest.raises(ValueError):
        IoManager().split_number(phone_number)


def test_message_whitespace_is_tidied():
    assert IoManager().parse_message("  Your   parcel\n is   waiting ") == "Your parcel is waiting"


@pytest.mark.parametrize("message", ["hi", "abc 123 !!!", "   ", "1234567890"])
def test_message_with_too_few_letters_is_rejected(message):
    with pytest.raises(ValueError):
        IoManager().parse_message(message)


def test_message_with_enough_letters_is_accepted():
    assert IoManager().parse_message("Hello there") == "Hello there"
