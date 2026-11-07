"""Tests for classes/record_converter.py. Run from the project folder with:

    python -m pytest tests/test_record_converter.py
"""

import pytest

from classes.record_converter import RecordConverter
from record import Record


def make_valid_dict() -> dict:
    """A complete, valid record in the same shape as scam_data.json."""
    return {
        "record_id": 1,
        "timestamp": "2026-10-02 11:40:00",
        "phone_number": "+6591234567",
        "country_code": "+65",
        "message_content": "Your account is suspended. Click http://bad.link",
        "scam_probability": 90,
        "risk_level": "HIGH",
        "scam_type": "Bank Impersonation Scam",
        "indicators": ["Urgent language", "Suspicious link"],
        "explanation": "Impersonates a bank.",
        "recommendation": "Do not click the link.",
    }


# ---------- from_dict / to_dict ----------

def test_valid_dict_becomes_record() -> None:
    record, error = RecordConverter.from_dict(make_valid_dict())
    assert error == ""
    assert isinstance(record, Record)
    assert record.risk_level == "HIGH"


def test_json_names_map_to_record_names() -> None:
    record, _error = RecordConverter.from_dict(make_valid_dict())
    assert record.record_id == 1
    assert record.message.startswith("Your account")     # JSON "message_content"


def test_round_trip_keeps_every_field() -> None:
    record, _error = RecordConverter.from_dict(make_valid_dict())
    assert RecordConverter.to_dict(record) == make_valid_dict()


def test_old_message_id_key_still_loads() -> None:
    data = make_valid_dict()
    data["message_id"] = data.pop("record_id")      # a file saved before the rename
    record, error = RecordConverter.from_dict(data)
    assert error == ""
    assert record.record_id == 1
    assert "message_id" not in RecordConverter.to_dict(record)   # saved with new name


def test_non_dict_is_rejected() -> None:
    assert RecordConverter.from_dict("garbage") == (None, "Record is not a dictionary.")


def test_from_dict_does_not_change_the_input() -> None:
    data = make_valid_dict()
    del data["country_code"]
    RecordConverter.from_dict(data)
    assert "country_code" not in data


# ---------- standardising (same rules as Phase 1) ----------

def test_risk_level_is_uppercased() -> None:
    data = make_valid_dict()
    data["risk_level"] = " High "
    record, _error = RecordConverter.from_dict(data)
    assert record.risk_level == "HIGH"


def test_country_code_is_derived_from_phone() -> None:
    data = make_valid_dict()
    del data["country_code"]
    record, _error = RecordConverter.from_dict(data)
    assert record.country_code == "+65"


def test_unreadable_phone_gives_unknown_country() -> None:
    assert RecordConverter.country_code_from_phone("91234567") == "Unknown"
    assert RecordConverter.country_code_from_phone("hello") == "Unknown"


def test_missing_optional_fields_get_defaults() -> None:
    data = make_valid_dict()
    del data["explanation"]
    del data["indicators"]
    record, error = RecordConverter.from_dict(data)
    assert error == ""
    assert record.explanation == ""
    assert record.indicators == []


# ---------- validation (invalid data is rejected) ----------

@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("risk_level", "VERY HIGH"),
        ("risk_level", "Unknown"),
        ("scam_probability", 150),
        ("scam_probability", -1),
        ("scam_probability", "90"),
        ("scam_probability", True),      # bool must be rejected
        ("record_id", True),
        ("record_id", -5),
        ("message_content", "   "),
        ("indicators", "not a list"),
        ("scam_type", 42),
    ],
)
def test_invalid_values_are_rejected(field: str, bad_value: object) -> None:
    data = make_valid_dict()
    data[field] = bad_value
    record, error = RecordConverter.from_dict(data)
    assert record is None
    assert error != ""


def test_missing_message_content_is_rejected() -> None:
    data = make_valid_dict()
    del data["message_content"]
    assert RecordConverter.from_dict(data) == (None, "message_content cannot be empty.")


# ---------- checking Record objects built elsewhere ----------

def test_check_valid_record() -> None:
    record, _error = RecordConverter.from_dict(make_valid_dict())
    assert RecordConverter.check_record(record) == (True, "")


def test_check_unfinished_record_fails() -> None:
    # Record() with its defaults: no id, no message, empty risk level.
    ok, _error = RecordConverter.check_record(Record())
    assert ok is False


def test_check_non_record_fails() -> None:
    assert RecordConverter.check_record({"a": 1}) == (False, "Only Record objects can be saved.")