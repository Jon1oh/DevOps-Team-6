"""Tests for the Data Manager side of the app (Part 2).

Covers:
- DataManager: saving, finding, removing, ids, risk counts, summary, rollback
- JsonRecordStorage: missing, empty, corrupt and wrongly formatted files,
  recovery from the backup file
- RecordConverter: validation and standardising rules
- ScamStatisticsCalculator: counts, percentages, most common values

Every test uses pytest's tmp_path (a fresh temporary folder), so the real
files in /data are never touched. No AI API is used.

Run from the project root:  python -m pytest tests/test_data_manager.py -v
"""

import json

import pytest

from managers.data_manager import DataManager
from app.models.record import Record
from app.storage.json_record_storage import JsonRecordStorage
from app.storage.record_converter import RecordConverter
from app.interfaces.record_storage import RecordStorage
from app.storage.scam_statistics_calculator import ScamStatisticsCalculator


# ======================================================================
# Test helpers
# ======================================================================

class InMemoryRecordStorage(RecordStorage):
    """A storage that keeps records in a list instead of a file.

    Used to show that DataManager works with ANY RecordStorage child
    (polymorphism / LSP), and to simulate a save that fails.
    """

    def __init__(self, records=None, fail_saves=False):
        super().__init__()
        self._saved = list(records or [])
        self.fail_saves = fail_saves
        self.save_calls = 0

    def load(self):
        return list(self._saved)

    def save_all(self, records):
        self.save_calls += 1
        if self.fail_saves:
            return False, "Could not write to the data file."
        self._saved = list(records)
        return True, ""


def ai_output(**changes) -> dict:
    """A valid dictionary shaped like the final AI output that app.py saves."""
    data = {
        "timestamp": "2026-11-15 10:00:00",
        "phone_number": "91234567",
        "country_code": "+65",
        "message_content": "You won $5,000! Click http://cashprice-govsg.com",
        "scam_probability": 96,
        "risk_level": "HIGH",
        "scam_type": "Unexpected Prize Money Scam",
        "indicators": ["Suspicious links", "Unexpected prizes or winnings"],
        "explanation": "Claims a prize the user never entered for.",
        "recommendation": "Do not click the link.",
    }
    data.update(changes)
    return data


def saved_entry(record_id: int, **changes) -> dict:
    """A valid entry as it appears inside scam_data.json."""
    entry = ai_output(**changes)
    entry["record_id"] = record_id
    return entry


@pytest.fixture
def paths(tmp_path):
    """Main data file and backup file inside a fresh temporary folder."""
    return tmp_path / "scam_data.json", tmp_path / "backup_database.json"


def write_json(path, content) -> None:
    path.write_text(json.dumps(content), encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_manager(paths) -> DataManager:
    """A DataManager using the real JSON storage on the temporary files."""
    data_file, backup_file = paths
    return DataManager(JsonRecordStorage(str(data_file), str(backup_file)))


# ======================================================================
# DataManager: saving records
# ======================================================================

def test_new_manager_with_no_files_starts_empty(paths):
    manager = json_manager(paths)
    assert manager.records == []
    assert manager.next_id() == 1


def test_save_record_adds_record_and_writes_file(paths):
    manager = json_manager(paths)

    assert manager.save_record(ai_output()) == (True, "")

    record = manager.find_record(1)
    assert record.risk_level == "HIGH"
    assert record.message.startswith("You won")
    saved = read_json(paths[0])
    assert [entry["record_id"] for entry in saved] == [1]


def test_records_are_loaded_again_in_a_new_run(paths):
    first_run = json_manager(paths)
    first_run.save_record(ai_output())
    first_run.save_record(ai_output(risk_level="LOW", scam_probability=10))

    second_run = json_manager(paths)

    assert [record.record_id for record in second_run.records] == [1, 2]
    assert second_run.find_record(2).risk_level == "LOW"


def test_record_ids_go_up_and_any_given_id_is_ignored(paths):
    manager = json_manager(paths)
    manager.save_record(ai_output(record_id=99))     # id in the data is ignored
    manager.save_record(ai_output())

    assert [record.record_id for record in manager.records] == [1, 2]
    assert manager.next_id() == 3


def test_save_record_does_not_change_the_callers_dictionary(paths):
    manager = json_manager(paths)
    data = ai_output()
    original = dict(data)

    manager.save_record(data)

    assert data == original
    assert "record_id" not in data


@pytest.mark.parametrize(
    "bad_data, expected_error",
    [
        ("not a dictionary", "Record is not a dictionary."),
        (ai_output(risk_level="EXTREME"), "risk_level must be HIGH, MEDIUM or LOW."),
        (ai_output(scam_probability=150), "scam_probability must be between 0 and 100."),
        (ai_output(scam_probability=-1), "scam_probability must be between 0 and 100."),
        (ai_output(message_content="   "), "message_content cannot be empty."),
        (ai_output(indicators="Suspicious links"), "Wrong type for field: indicators"),
        (ai_output(scam_probability="96"), "Wrong type for field: scam_probability"),
    ],
)
def test_invalid_data_is_rejected_and_nothing_is_saved(paths, bad_data, expected_error):
    manager = json_manager(paths)
    manager.save_record(ai_output())                 # one good record first

    ok, message = manager.save_record(bad_data)

    assert (ok, message) == (False, expected_error)
    assert len(manager.records) == 1
    assert len(read_json(paths[0])) == 1             # file unchanged


# ======================================================================
# DataManager: finding, removing and reading
# ======================================================================

def test_find_record_returns_none_for_unknown_id(paths):
    manager = json_manager(paths)
    manager.save_record(ai_output())
    assert manager.find_record(42) is None


def test_remove_record_deletes_it_from_memory_and_file(paths):
    manager = json_manager(paths)
    manager.save_record(ai_output())
    manager.save_record(ai_output())

    assert manager.remove_record(1) == (True, "")

    assert [record.record_id for record in manager.records] == [2]
    assert [entry["record_id"] for entry in read_json(paths[0])] == [2]


def test_remove_record_with_unknown_id_fails_safely(paths):
    manager = json_manager(paths)
    manager.save_record(ai_output())

    assert manager.remove_record(42) == (False, "No record with record_id 42.")
    assert len(manager.records) == 1


def test_records_property_returns_a_copy(paths):
    manager = json_manager(paths)
    manager.save_record(ai_output())

    outside_list = manager.records
    outside_list.clear()                             # changing the copy...

    assert len(manager.records) == 1                 # ...does not change DataManager


def test_count_risk_levels_for_one_phone_number(paths):
    manager = json_manager(paths)
    manager.save_record(ai_output(risk_level="HIGH", scam_probability=90))
    manager.save_record(ai_output(risk_level="HIGH", scam_probability=85))
    manager.save_record(ai_output(risk_level="LOW", scam_probability=10))
    manager.save_record(ai_output(phone_number="88887777", risk_level="MEDIUM", scam_probability=60))

    assert manager.count_risk_levels("91234567") == {"HIGH": 2, "MEDIUM": 0, "LOW": 1}
    assert manager.count_risk_levels("88887777") == {"HIGH": 0, "MEDIUM": 1, "LOW": 0}
    assert manager.count_risk_levels("00000000") == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}


def test_summary_of_saved_records(paths):
    manager = json_manager(paths)
    manager.save_record(ai_output(risk_level="HIGH", scam_type="Banking Scam"))
    manager.save_record(ai_output(risk_level="HIGH", scam_type="Banking Scam"))
    manager.save_record(ai_output(risk_level="MEDIUM", scam_probability=60, scam_type="Job Scam"))
    manager.save_record(ai_output(risk_level="LOW", scam_probability=5, scam_type="Not Scam"))

    summary = manager.summary()

    assert summary["total_messages"] == 4
    assert summary["risk_level_breakdown"] == {"HIGH": 2, "MEDIUM": 1, "LOW": 1}
    assert summary["risk_level_percentage"] == {"HIGH": 50.0, "MEDIUM": 25.0, "LOW": 25.0}
    assert summary["most_common_scam"] == "Banking Scam"
    assert summary["most_common_origin"] == ("+65", 100.0)


def test_summary_with_no_records(paths):
    summary = json_manager(paths).summary()
    assert summary["total_messages"] == 0
    assert summary["most_common_scam"] == "Unknown"
    assert summary["risk_level_percentage"] == {}


# ======================================================================
# DataManager works with any storage, and rolls back failed saves
# ======================================================================

def test_data_manager_works_with_a_different_storage_class():
    """Same DataManager code, different RecordStorage child (polymorphism / LSP)."""
    storage = InMemoryRecordStorage()
    manager = DataManager(storage)

    assert manager.save_record(ai_output()) == (True, "")
    assert manager.remove_record(1) == (True, "")
    assert storage.save_calls == 2


def test_failed_save_does_not_keep_the_new_record():
    storage = InMemoryRecordStorage(fail_saves=True)
    manager = DataManager(storage)

    ok, message = manager.save_record(ai_output())

    assert ok is False
    assert message == "Could not write to the data file."
    assert manager.records == []                     # memory still matches storage


def test_failed_remove_puts_the_record_back_in_the_same_place():
    existing = [
        RecordConverter.from_dict(saved_entry(record_id))[0] for record_id in (1, 2, 3)
    ]
    storage = InMemoryRecordStorage(existing)
    manager = DataManager(storage)
    storage.fail_saves = True

    ok, _message = manager.remove_record(2)

    assert ok is False
    assert [record.record_id for record in manager.records] == [1, 2, 3]


def test_record_storage_is_abstract():
    with pytest.raises(TypeError):
        RecordStorage()


# ======================================================================
# JsonRecordStorage: missing, empty and corrupt files
# ======================================================================

def test_missing_main_file_is_restored_from_backup(paths):
    data_file, backup_file = paths
    write_json(backup_file, [saved_entry(1), saved_entry(2)])

    manager = json_manager(paths)

    assert [record.record_id for record in manager.records] == [1, 2]
    assert "missing" in manager.status_message
    assert "Restored 2 record(s) from backup" in manager.status_message
    assert len(read_json(data_file)) == 2            # main file rewritten


def test_missing_main_file_and_missing_backup(paths):
    manager = json_manager(paths)
    assert manager.records == []
    assert "No valid backup records were available" in manager.status_message


def test_empty_main_file_is_restored_from_backup(paths):
    data_file, backup_file = paths
    data_file.write_text("", encoding="utf-8")       # 0-byte file
    write_json(backup_file, [saved_entry(1)])

    manager = json_manager(paths)

    assert [record.record_id for record in manager.records] == [1]
    assert "empty" in manager.status_message


def test_corrupt_main_file_is_preserved_and_restored_from_backup(paths):
    data_file, backup_file = paths
    data_file.write_text('[{"record_id": 1, "timestamp": ', encoding="utf-8")
    write_json(backup_file, [saved_entry(1)])

    manager = json_manager(paths)

    assert [record.record_id for record in manager.records] == [1]
    assert "corrupt" in manager.status_message
    assert (data_file.parent / "scam_data.corrupt.json").exists()   # evidence kept
    assert len(read_json(data_file)) == 1


def test_main_file_with_wrong_format_is_restored_from_backup(paths):
    data_file, backup_file = paths
    write_json(data_file, {"record_id": 1})          # a dictionary, not a list
    write_json(backup_file, [saved_entry(1)])

    manager = json_manager(paths)

    assert [record.record_id for record in manager.records] == [1]
    assert "wrong format" in manager.status_message


def test_corrupt_main_file_and_corrupt_backup_does_not_crash(paths):
    data_file, backup_file = paths
    data_file.write_text("{{ not json", encoding="utf-8")
    backup_file.write_text("also not json", encoding="utf-8")

    manager = json_manager(paths)

    assert manager.records == []
    assert "No valid backup records were available" in manager.status_message


def test_invalid_entries_are_skipped_and_reported(paths):
    data_file, _backup_file = paths
    write_json(data_file, [
        saved_entry(1),
        saved_entry(2, risk_level="EXTREME"),        # invalid
        "not a record",                              # invalid
    ])

    manager = json_manager(paths)

    assert [record.record_id for record in manager.records] == [1]
    assert manager.status_message == "Skipped 2 invalid record(s)."


def test_backup_file_is_updated_after_each_save(paths):
    _data_file, backup_file = paths
    manager = json_manager(paths)

    manager.save_record(ai_output())
    manager.save_record(ai_output())

    assert [entry["record_id"] for entry in read_json(backup_file)] == [1, 2]


# ======================================================================
# RecordConverter: standardising rules
# ======================================================================

def test_risk_level_is_upper_cased():
    record, error = RecordConverter.from_dict(saved_entry(1, risk_level=" high "))
    assert error == ""
    assert record.risk_level == "HIGH"


def test_missing_country_code_is_filled_from_phone_number():
    entry = saved_entry(1, phone_number="+6591234567")
    del entry["country_code"]

    record, _error = RecordConverter.from_dict(entry)

    assert record.country_code == "+65"


def test_true_or_false_is_not_accepted_as_a_number():
    _record, error = RecordConverter.from_dict(saved_entry(1, scam_probability=True))
    assert error == "Wrong type for field: scam_probability"


def test_record_to_dict_and_back_gives_the_same_data():
    record, _error = RecordConverter.from_dict(saved_entry(5))

    expected_entry = saved_entry(5)
    expected_entry["country_name"] = "Singapore"     # added 

    assert RecordConverter.to_dict(record) == expected_entry


# ======================================================================
# ScamStatisticsCalculator
# ======================================================================

def test_percentages_are_rounded_to_two_decimal_places():
    calculator = ScamStatisticsCalculator()
    assert calculator.percentages({"A": 1, "B": 2}) == {"A": 33.33, "B": 66.67}


def test_percentages_of_nothing_is_empty():
    assert ScamStatisticsCalculator().percentages({}) == {}


def test_most_common_tie_is_broken_alphabetically():
    records = [
        RecordConverter.from_dict(saved_entry(1, scam_type="Job Scam"))[0],
        RecordConverter.from_dict(saved_entry(2, scam_type="Banking Scam"))[0],
    ]
    assert ScamStatisticsCalculator().most_common(records, "scam_type") == ("Banking Scam", 50.0)


def test_country_label_shows_country_name():
    calculator = ScamStatisticsCalculator()
    assert calculator.country_label("+65") == "+65 (Singapore)"
    assert calculator.country_name("not a code") == "Unknown"
