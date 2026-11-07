"""Tests for json_record_storage.py. Run from the project folder with:

    python -m pytest tests/test_json_record_storage.py

Every test uses pytest's tmp_path: a fresh, empty folder that pytest creates
for that one test. The real data/ folder is never touched.
"""

import json
import os

import pytest

from classes.json_record_storage import JsonRecordStorage
from record import Record
from classes.record_converter import RecordConverter


def make_valid_dict(record_id: int = 1) -> dict:
    return {
        "record_id": record_id,
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


def make_record(record_id: int = 1) -> Record:
    record, _error = RecordConverter.from_dict(make_valid_dict(record_id))
    return record


def make_storage(tmp_path) -> JsonRecordStorage:
    """A storage object pointing at files inside this test's own folder."""
    return JsonRecordStorage(
        data_file=str(tmp_path / "scam_data.json"),
        backup_file=str(tmp_path / "backup_database.json"),
    )


def write_text(path, text: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)


def read_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------- loading normal and broken main files ----------

def test_valid_file_loads_records(tmp_path) -> None:
    write_text(tmp_path / "scam_data.json", json.dumps([make_valid_dict()]))
    storage = make_storage(tmp_path)

    records = storage.load()

    assert len(records) == 1
    assert isinstance(records[0], Record)
    assert storage.status_message == ""


def test_missing_file_returns_empty_list(tmp_path) -> None:
    storage = make_storage(tmp_path)
    assert storage.load() == []
    assert "missing" in storage.status_message


def test_zero_byte_file_is_empty_not_corrupt(tmp_path) -> None:
    write_text(tmp_path / "scam_data.json", "")
    storage = make_storage(tmp_path)

    assert storage.load() == []
    assert "empty" in storage.status_message
    assert not os.path.exists(tmp_path / "scam_data.corrupt.json")


def test_corrupt_file_is_preserved(tmp_path) -> None:
    write_text(tmp_path / "scam_data.json", "{ this is not valid json")
    storage = make_storage(tmp_path)

    assert storage.load() == []
    assert "corrupt" in storage.status_message
    assert os.path.exists(tmp_path / "scam_data.corrupt.json")


def test_non_list_file_is_preserved(tmp_path) -> None:
    write_text(tmp_path / "scam_data.json", '{"not": "a list"}')
    storage = make_storage(tmp_path)

    assert storage.load() == []
    assert "wrong format" in storage.status_message
    assert os.path.exists(tmp_path / "scam_data.corrupt.json")


def test_invalid_entries_are_skipped_and_counted(tmp_path) -> None:
    bad_risk = make_valid_dict(2)
    bad_risk["risk_level"] = "Unknown"
    entries = [make_valid_dict(1), "garbage", 42, bad_risk]
    write_text(tmp_path / "scam_data.json", json.dumps(entries))
    storage = make_storage(tmp_path)

    records = storage.load()

    assert len(records) == 1
    assert storage.status_message == "Skipped 3 invalid record(s)."


# ---------- recovery from the backup ----------

def test_empty_main_restores_from_backup(tmp_path) -> None:
    write_text(tmp_path / "scam_data.json", "[]")
    write_text(tmp_path / "backup_database.json", json.dumps([make_valid_dict()]))
    storage = make_storage(tmp_path)

    records = storage.load()

    assert len(records) == 1
    assert "Restored 1 record(s)" in storage.status_message
    assert len(read_json(tmp_path / "scam_data.json")) == 1   # main file rewritten


def test_corrupt_main_restores_from_backup(tmp_path) -> None:
    write_text(tmp_path / "scam_data.json", "{ invalid JSON")
    write_text(tmp_path / "backup_database.json", json.dumps([make_valid_dict()]))
    storage = make_storage(tmp_path)

    records = storage.load()

    assert len(records) == 1
    assert "corrupt" in storage.status_message
    assert "Restored" in storage.status_message


def test_invalid_backup_records_are_not_restored(tmp_path) -> None:
    bad = make_valid_dict()
    bad["risk_level"] = "UNKNOWN"
    write_text(tmp_path / "backup_database.json", json.dumps([bad]))
    storage = make_storage(tmp_path)

    assert storage.load() == []
    assert "No valid backup records" in storage.status_message


def test_corrupt_backup_does_not_crash(tmp_path) -> None:
    write_text(tmp_path / "scam_data.json", "{ invalid JSON")
    write_text(tmp_path / "backup_database.json", "{ also broken")
    storage = make_storage(tmp_path)

    assert storage.load() == []
    assert "No valid backup records" in storage.status_message


# ---------- saving ----------

def test_save_then_load(tmp_path) -> None:
    storage = make_storage(tmp_path)

    assert storage.save(make_record()) == (True, "")
    assert len(storage.load()) == 1


def test_save_updates_main_and_backup(tmp_path) -> None:
    storage = make_storage(tmp_path)
    storage.save(make_record())

    main_entries = read_json(tmp_path / "scam_data.json")
    backup_entries = read_json(tmp_path / "backup_database.json")
    assert len(main_entries) == 1
    assert main_entries == backup_entries


def test_save_rejects_non_record(tmp_path) -> None:
    storage = make_storage(tmp_path)
    ok, message = storage.save(make_valid_dict())   # a dict, not a Record
    assert ok is False
    assert message == "Only Record objects can be saved."


def test_backup_failure_is_a_warning_not_an_error(tmp_path) -> None:
    # A folder with the backup's name means the backup file cannot be written.
    os.makedirs(tmp_path / "backup_database.json")
    storage = make_storage(tmp_path)

    ok, message = storage.save(make_record())

    assert ok is True
    assert "backup database could not be updated" in message
    assert len(read_json(tmp_path / "scam_data.json")) == 1


def test_main_file_failure_is_reported(tmp_path) -> None:
    # A folder with the main file's name means it cannot be written.
    os.makedirs(tmp_path / "scam_data.json")
    storage = make_storage(tmp_path)

    ok, message = storage.save(make_record())

    assert ok is False
    assert message == "Could not write to the data file."


# ---------- message ids ----------

def test_next_id_starts_at_one(tmp_path) -> None:
    assert make_storage(tmp_path).next_id() == 1


def test_next_id_is_highest_plus_one(tmp_path) -> None:
    entries = [make_valid_dict(3), make_valid_dict(7)]
    write_text(tmp_path / "scam_data.json", json.dumps(entries))
    assert make_storage(tmp_path).next_id() == 8


def test_status_message_is_read_only(tmp_path) -> None:
    storage = make_storage(tmp_path)
    with pytest.raises(AttributeError):    # no setter, so assigning fails
        storage.status_message = "hacked"