# Test script for data_manager.py
#
# This file has two parts:
#   1. Automated tests  - functions starting with test_ check the results with assert
#   2. Demo             - prints the summary of the real scam_data.json so we can see it
#
# Run with either:
#   python test_data_manager.py                 (runs the tests, then shows the demo)
#   python -m pytest test_data_manager.py -v    (runs the tests only)
#
# Plain functions only (no classes - project is 100% procedural).
# The tests use temporary files, so the real scam_data.json is never changed.

import json
import os
import tempfile

import data_manager as dm

REAL_DATA_FILE = dm.DATA_FILE   # remembered so the demo can switch back to it


# =====================================================================
# PART 1: AUTOMATED TESTS
# =====================================================================


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


def test_standardize_uppercases_risk_level() -> None:
    fixed = dm.standardize_record({"risk_level": "High", "phone_number": "+6591234567"})
    assert fixed["risk_level"] == "HIGH"
    assert fixed["country_code"] == "+65"


def test_country_code_from_phone() -> None:
    assert dm.get_country_code("+6591234567") == "+65"
    assert dm.get_country_code("+2348012345678") == "+234"
    assert dm.get_country_code("+819012345678") == "+81"      # Japan - not in the old fixed list
    assert dm.get_country_code("91234567") == "Unknown"       # no + country code
    assert dm.get_country_code("hello") == "Unknown"


def test_country_name_from_code() -> None:
    assert dm.get_country_name("+65") == "Singapore"
    assert dm.get_country_name("+81") == "Japan"
    assert dm.get_country_name("+999") == "Unknown"
    assert dm.get_country_name("Unknown") == "Unknown"


def test_country_name_for_number() -> None:
    assert dm.get_country_name_for_number("+14155550123") == "United States"
    assert dm.get_country_name_for_number("+16135550123") == "Canada"   # same +1 code
    assert dm.get_country_name_for_number("abc") == "Unknown"


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


# ---------- message_id ----------

def test_next_message_id() -> None:
    assert dm.get_next_message_id([]) == 1
    assert dm.get_next_message_id([{"message_id": 3}, {"message_id": 7}]) == 8
    assert dm.get_next_message_id([{"message_id": "x"}, "corrupt"]) == 1


def test_save_assigns_message_ids_in_order() -> None:
    use_temp_file(None)
    dm.save_record(make_valid_record())
    dm.save_record(make_valid_record())     # same input id (1) on purpose
    ids = [record["message_id"] for record in dm.load_records()]
    assert ids == [1, 2]                     # no duplicates


# ---------- country name ----------

def test_country_label() -> None:
    assert dm.get_country_label("+65") == "+65 (Singapore)"
    assert dm.get_country_label("+999") == "+999 (Unknown)"


def test_summary_has_country_labels() -> None:
    records = [{"risk_level": "HIGH", "scam_type": "Phishing", "country_code": "+44"}]
    summary = dm.summary_with_percentages(records)
    assert summary["origin_country_labels"] == {"+44": "+44 (United Kingdom)"}


# ---------- count_risk_levels ----------

def test_count_risk_levels_for_one_number() -> None:
    records = [
        {"phone_number": "+6591234567", "risk_level": "HIGH"},
        {"phone_number": "+6591234567", "risk_level": "LOW"},
        {"phone_number": "+6500000000", "risk_level": "HIGH"},
    ]
    use_temp_file(json.dumps(records))
    assert dm.count_risk_levels("+6591234567") == {"HIGH": 1, "MEDIUM": 0, "LOW": 1}
    assert dm.count_risk_levels("+6599999999") == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}


# =====================================================================
# PART 2: DEMO - display the real data (not run by pytest)
# =====================================================================

def print_all_records(records: list[dict]) -> None:
    """Print every record in a readable format."""
    for record in records:
        print("\n========================================")
        print(f"          SCAM INCIDENT RECORD {record['message_id']} ")
        print("========================================")
        print(f"Time stamp       : {record['timestamp']}")
        print(f"Phone Number     : {record['phone_number']}")
        print(f"Country          : {dm.get_country_label(record['country_code'])}")
        print(f"Risk Level       : {record['risk_level']}")
        print(f"Scam Probability : {record['scam_probability']}%")
        print(f"Scam Type        : {record['scam_type']}")
        print(f"Message          : {record['message_content']}")
        print(f"Indicators       : {', '.join(record['indicators'])}")
        print(f"Explanation      : {record['explanation']}")
        print(f"Recommendation   : {record['recommendation']}")


def print_message_summary(summary: dict) -> None:
    """Print the summary returned by summary_with_percentages()."""
    print("\n==============================")
    print("      SCAM MESSAGE SUMMARY")
    print("==============================\n")
    print(f"Total messages: {summary['total_messages']}\n")

    print("Risk Level Breakdown")
    print("------------------------------")
    for risk_level, count in summary["risk_level_breakdown"].items():
        percent = summary["risk_level_percentage"].get(risk_level, 0)
        print(f"{risk_level}: {count} ({percent}%)")

    print()
    print("Scam Category Breakdown")
    print("------------------------------")
    for scam_type, count in summary["scam_category_breakdown"].items():
        percent = summary["scam_category_percentage"].get(scam_type, 0)
        print(f"{scam_type}: {count} ({percent}%)")

    print()
    print("Country of Origin Breakdown")
    print("------------------------------")
    for country_code, count in summary["origin_country_breakdown"].items():
        percent = summary["origin_country_percentage"].get(country_code, 0)
        label = summary["origin_country_labels"][country_code]
        print(f"{label}: {count} ({percent}%)")

    print()
    print("Most Common type of Scam")
    print("------------------------------")
    print(summary["most_common_scam"])


def run_all_tests() -> int:
    """Run every test_ function and print PASS/FAIL. Returns the number of failures."""
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
    return failed


def run_demo() -> None:
    """Load the real scam_data.json and print its summary (read-only)."""
    dm.DATA_FILE = REAL_DATA_FILE
    scam_records = dm.load_records()
    # print_all_records(scam_records)    # uncomment to see every record
    print_message_summary(dm.summary_with_percentages(scam_records))


if __name__ == "__main__":
    run_all_tests()
    run_demo()