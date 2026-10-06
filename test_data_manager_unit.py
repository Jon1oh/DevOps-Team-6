# Automated tests for data_manager.py
#
# Can run with either:
#   python3 -m pytest test_data_manager_unit.py -v
#   python3 test_data_manager_unit.py
#

import json
import os
import tempfile

import data_manager as dm


def use_temp_file(contents: str | None) -> str:
    """Point data_manager at a fresh temporary file (optionally with contents)."""
    folder = tempfile.mkdtemp()
    path = os.path.join(folder, "scam_data.json")
    if contents is not None:
        with open(path, "w", encoding="utf-8") as file:
            file.write(contents)
    dm.DATA_FILE = path
    return path


def make_valid_record() -> dict:
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


SAMPLE_RECORDS = [
    {"country_code": "+65", "scam_type": "Phishing"},
    {"country_code": "+65", "scam_type": "Phishing"},
    {"country_code": "+60", "scam_type": "Delivery"},
    {"country_code": "+65", "scam_type": "Job scam"},
]


# ---------- percentage / most-common ----------

def test_percentage_basic() -> None:
    assert dm.calculate_percentage({"A": 3, "B": 1}) == {"A": 75.0, "B": 25.0}


def test_percentage_empty() -> None:
    assert dm.calculate_percentage({}) == {}


def test_percentage_rounding() -> None:
    assert dm.calculate_percentage({"A": 1, "B": 2}) == {"A": 33.33, "B": 66.67}


def test_most_common_origin() -> None:
    assert dm.get_most_common_origin(SAMPLE_RECORDS) == ("+65", 75.0)
    assert dm.get_most_common_origin([]) is None


def test_most_common_scam_type() -> None:
    assert dm.get_most_common_scam_type(SAMPLE_RECORDS) == ("Phishing", 50.0)
    assert dm.get_most_common_scam_type([]) is None


def test_tie_is_alphabetical() -> None:
    tie = [{"scam_type": "Phishing"}, {"scam_type": "Delivery"}]
    assert dm.get_most_common_scam_type(tie) == ("Delivery", 50.0)


# ---------- schema ----------

def test_valid_record_passes() -> None:
    assert dm.validate_record(make_valid_record()) == (True, "")


def test_missing_field_fails() -> None:
    record = make_valid_record()
    del record["scam_type"]
    assert dm.validate_record(record) == (False, "Missing field: scam_type")


def test_wrong_type_fails() -> None:
    record = make_valid_record()
    record["scam_probability"] = "90"
    assert dm.validate_record(record)[0] is False


def test_bad_risk_level_fails() -> None:
    record = make_valid_record()
    record["risk_level"] = "VERY HIGH"
    assert dm.validate_record(record)[0] is False


def test_probability_out_of_range_fails() -> None:
    record = make_valid_record()
    record["scam_probability"] = 150
    assert dm.validate_record(record)[0] is False


def test_standardize_renames_old_keys() -> None:
    old = {"time_stamp": "2026-10-02", "scam_probability (%)": 80, "risk_level": "High"}
    fixed = dm.standardize_record(old)
    assert fixed["timestamp"] == "2026-10-02"
    assert fixed["scam_probability"] == 80
    assert fixed["risk_level"] == "HIGH"
    assert "time_stamp" not in fixed


def test_country_code_from_phone() -> None:
    assert dm.get_country_code("+6591234567") == "+65"
    assert dm.get_country_code("+2348012345678") == "+234"
    assert dm.get_country_code("91234567") == "Unknown"
    assert dm.get_country_name("+65") == "Singapore"


# ---------- corrupt JSON handling ----------

def test_missing_file_returns_empty() -> None:
    use_temp_file(None)
    assert dm.load_records() == []


def test_corrupt_file_is_backed_up() -> None:
    path = use_temp_file("{ this is not valid json")
    records, status = dm.load_records_with_status()
    assert records == []
    assert "corrupt" in status
    assert os.path.exists(path.replace(".json", ".corrupt.json"))


def test_non_list_file_is_handled() -> None:
    use_temp_file('{"not": "a list"}')
    assert dm.load_records() == []


def test_corrupt_entries_are_skipped() -> None:
    use_temp_file(json.dumps([make_valid_record(), "garbage", 42]))
    records, status = dm.load_records_with_status()
    assert len(records) == 1
    assert "Skipped 2" in status


def test_summary_survives_records_missing_keys() -> None:
    use_temp_file(json.dumps([{"phone_number": "+6591234567"}]))
    records = dm.load_records()
    summary = dm.summary_with_percentages(records)
    assert summary["total_messages"] == 1


def test_save_then_load() -> None:
    use_temp_file(None)
    assert dm.save_record(make_valid_record()) == (True, "")
    assert len(dm.load_records()) == 1


def test_invalid_record_is_not_saved() -> None:
    use_temp_file(None)
    bad = make_valid_record()
    bad["message_content"] = ""
    ok, _error = dm.save_record(bad)
    assert ok is False
    assert dm.load_records() == []


# ---------- lets the file run without pytest ----------

if __name__ == "__main__":
    all_tests = [value for name, value in list(globals().items())
                 if name.startswith("test_") and callable(value)]
    failed = 0
    for test in all_tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError:
            print(f"FAIL  {test.__name__}")
            failed += 1
    print(f"\n{len(all_tests) - failed}/{len(all_tests)} tests passed")