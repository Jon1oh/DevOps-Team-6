"""Tests for models/scam_record.py. Run from the project folder with:
 
    python -m pytest tests/test_scam_record.py
"""
 
import pytest
 
from classes.scam_record import ScamRecord
 
 
def make_valid_dict() -> dict:
    """A complete, valid record in the same shape as scam_data.json."""
    return {
        "message_id": 1,
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
    record, error = ScamRecord.from_dict(make_valid_dict())
    assert error == ""
    assert record.risk_level == "HIGH"
    assert record.message_content.startswith("Your account")
 
 
def test_round_trip_keeps_every_field() -> None:
    record, _error = ScamRecord.from_dict(make_valid_dict())
    assert record.to_dict() == make_valid_dict()
 
 
def test_non_dict_is_rejected() -> None:
    record, error = ScamRecord.from_dict("garbage")
    assert record is None
    assert error == "Record is not a dictionary."
 
 
def test_from_dict_does_not_change_the_input() -> None:
    data = make_valid_dict()
    del data["country_code"]
    ScamRecord.from_dict(data)
    assert "country_code" not in data
 
 
# ---------- standardising (same rules as Phase 1) ----------
 
def test_risk_level_is_uppercased() -> None:
    data = make_valid_dict()
    data["risk_level"] = " High "
    record, _error = ScamRecord.from_dict(data)
    assert record.risk_level == "HIGH"
 
 
def test_country_code_is_derived_from_phone() -> None:
    data = make_valid_dict()
    del data["country_code"]
    record, _error = ScamRecord.from_dict(data)
    assert record.country_code == "+65"
 
 
def test_unreadable_phone_gives_unknown_country() -> None:
    assert ScamRecord.country_code_from_phone("91234567") == "Unknown"
    assert ScamRecord.country_code_from_phone("hello") == "Unknown"
 
 
def test_missing_optional_fields_get_defaults() -> None:
    data = make_valid_dict()
    del data["explanation"]
    del data["indicators"]
    record, error = ScamRecord.from_dict(data)
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
        ("message_id", True),
        ("message_id", -5),
        ("message_content", "   "),
        ("indicators", "not a list"),
        ("scam_type", 42),
    ],
)
def test_invalid_values_are_rejected(field: str, bad_value: object) -> None:
    data = make_valid_dict()
    data[field] = bad_value
    record, error = ScamRecord.from_dict(data)
    assert record is None
    assert error != ""
 
 
def test_missing_message_content_is_rejected() -> None:
    data = make_valid_dict()
    del data["message_content"]
    record, error = ScamRecord.from_dict(data)
    assert record is None
    assert error == "message_content cannot be empty."
 
 
def test_setter_blocks_bad_value_on_existing_record() -> None:
    record, _error = ScamRecord.from_dict(make_valid_dict())
    with pytest.raises(ValueError):
        record.scam_probability = 500
    assert record.scam_probability == 90   # old value is kept
 
 
# ---------- encapsulation ----------
 
def test_indicators_cannot_be_changed_from_outside() -> None:
    record, _error = ScamRecord.from_dict(make_valid_dict())
    outside_copy = record.indicators
    outside_copy.append("Sneaky change")
    assert "Sneaky change" not in record.indicators
 