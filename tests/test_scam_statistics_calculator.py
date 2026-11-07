"""Tests for scam_statistics_calculator.py. Run from the project folder with:
 
    python -m pytest tests/test_scam_statistics_calculator.py
 
No files are used: the calculator only works on Record objects in memory.
"""
from classes.record_converter import RecordConverter
from record import Record
from classes.scam_statistics_calculator import ScamStatisticsCalculator
 
 
def make_record(country_code: str = "+65", scam_type: str = "Phishing",
                risk_level: str = "HIGH") -> Record:
    record, _error = RecordConverter.from_dict({
        "record_id": 1,
        "timestamp": "2026-10-02 11:40:00",
        "phone_number": "+6591234567",
        "country_code": country_code,
        "message_content": "Click this link now",
        "scam_probability": 90,
        "risk_level": risk_level,
        "scam_type": scam_type,
        "indicators": [],
        "explanation": "",
        "recommendation": "",
    })
    return record
 
 
def sample_records() -> list[Record]:
    """Same sample data as the Phase 1 tests."""
    return [
        make_record("+65", "Phishing"),
        make_record("+65", "Phishing"),
        make_record("+60", "Delivery"),
        make_record("+65", "Job scam"),
    ]
 
 
calculator = ScamStatisticsCalculator()
 
 
# ---------- percentages ----------
 
def test_percentages_basic() -> None:
    assert calculator.percentages({"A": 3, "B": 1}) == {"A": 75.0, "B": 25.0}
 
 
def test_percentages_empty() -> None:
    assert calculator.percentages({}) == {}
 
 
def test_percentages_round_to_two_places() -> None:
    assert calculator.percentages({"A": 1, "B": 2}) == {"A": 33.33, "B": 66.67}
 
 
# ---------- counting and most common ----------
 
def test_count_by_field() -> None:
    counts = calculator.count_by(sample_records(), "scam_type")
    assert counts == {"Phishing": 2, "Delivery": 1, "Job scam": 1}
 
 
def test_empty_value_counts_as_unknown() -> None:
    records = [make_record(scam_type=""), make_record(scam_type="Phishing")]
    assert calculator.count_by(records, "scam_type") == {"Unknown": 1, "Phishing": 1}
 
 
def test_non_records_are_ignored() -> None:
    records = [make_record(), "garbage", None]
    assert calculator.count_by(records, "risk_level") == {"HIGH": 1}
 
 
def test_most_common_origin() -> None:
    assert calculator.most_common(sample_records(), "country_code") == ("+65", 75.0)
 
 
def test_most_common_scam_type() -> None:
    assert calculator.most_common(sample_records(), "scam_type") == ("Phishing", 50.0)
 
 
def test_most_common_with_no_records() -> None:
    assert calculator.most_common([], "scam_type") is None
 
 
def test_tie_is_broken_alphabetically() -> None:
    records = [make_record(scam_type="Phishing"), make_record(scam_type="Delivery")]
    assert calculator.most_common(records, "scam_type") == ("Delivery", 50.0)
 
 
# ---------- country names ----------
 
def test_country_name() -> None:
    assert calculator.country_name("+65") == "Singapore"
    assert calculator.country_name("+81") == "Japan"
    assert calculator.country_name("+999") == "Unknown"
    assert calculator.country_name("Unknown") == "Unknown"
 
 
def test_country_label() -> None:
    assert calculator.country_label("+65") == "+65 (Singapore)"
    assert calculator.country_label("+999") == "+999 (Unknown)"
 
 
# ---------- full summary ----------
 
def test_summary_has_every_key_io_manager_needs() -> None:
    summary = calculator.summary(sample_records())
    expected_keys = {
        "total_messages",
        "risk_level_breakdown", "risk_level_percentage",
        "scam_category_breakdown", "scam_category_percentage",
        "origin_country_breakdown", "origin_country_percentage",
        "origin_country_labels",
        "most_common_scam", "most_common_scam_percentage", "most_common_origin",
    }
    assert set(summary.keys()) == expected_keys
 
 
def test_summary_values() -> None:
    summary = calculator.summary(sample_records())
    assert summary["total_messages"] == 4
    assert summary["most_common_scam"] == "Phishing"
    assert summary["most_common_scam_percentage"] == ("Phishing", 50.0)
    assert summary["most_common_origin"] == ("+65", 75.0)
    assert summary["origin_country_percentage"] == {"+65": 75.0, "+60": 25.0}
 
 
def test_summary_country_labels() -> None:
    summary = calculator.summary([make_record(country_code="+44")])
    assert summary["origin_country_labels"] == {"+44": "+44 (United Kingdom)"}
 
 
def test_summary_of_no_records() -> None:
    summary = calculator.summary([])
    assert summary["total_messages"] == 0
    assert summary["most_common_scam"] == "Unknown"
    assert summary["most_common_scam_percentage"] is None
    assert summary["most_common_origin"] is None
 