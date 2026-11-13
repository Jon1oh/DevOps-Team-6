"""Tests for SqliteRecordStorage (advanced feature: database integration).

Every test uses pytest's tmp_path, so it gets its own empty folder and never
touches the real files in /data. No live AI API is needed.

Run from the project root:  python -m pytest tests/test_sqlite_record_storage.py -v
"""

import json
import sqlite3
from contextlib import closing

import pytest

from managers.data_manager import DataManager
from models.record import Record
from storage.sqlite_record_storage import SqliteRecordStorage


# ----------------------------------------------------------------------
# Fixtures and helpers
# ----------------------------------------------------------------------

def make_record(record_id: int, risk_level: str = "HIGH", probability: int = 96) -> Record:
    """A valid Record, like the ones the AI analysis produces."""
    return Record(
        record_id=record_id,
        timestamp="2026-11-13 10:00:00",
        phone_number="+6591234567",
        country_code="+65",
        message=f"Test scam message number {record_id}",
        scam_probability=probability,
        risk_level=risk_level,
        scam_type="Prize Scam",
        indicators=["Suspicious link", "Unexpected prize claim"],
        explanation="Claims a prize the user never entered for.",
        recommendation="Do not click the link.",
    )


def ai_output() -> dict:
    """A dictionary shaped like the final AI output that app.py saves."""
    return {
        "timestamp": "2026-11-13 10:00:00",
        "phone_number": "+6591234567",
        "country_code": "+65",
        "message_content": "You won $5,000! Click http://cashprice-govsg.com",
        "scam_probability": 96,
        "risk_level": "HIGH",
        "scam_type": "Prize Scam",
        "indicators": ["Suspicious link"],
        "explanation": "Fake prize.",
        "recommendation": "Do not click the link.",
    }


@pytest.fixture
def paths(tmp_path):
    """Database and backup paths inside a fresh temporary folder."""
    return tmp_path / "scam_data.db", tmp_path / "backup_database.json"


@pytest.fixture
def storage(paths):
    db_file, backup_file = paths
    return SqliteRecordStorage(str(db_file), str(backup_file))


def count_rows(db_file) -> int:
    with closing(sqlite3.connect(db_file)) as connection:   # closed, so Windows can rename the file
        return connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]


# ----------------------------------------------------------------------
# CRUD at the storage level
# ----------------------------------------------------------------------

def test_new_database_with_no_backup_starts_empty(storage, paths):
    assert storage.load() == []
    assert storage.status_message == ""          # an empty new database is normal
    assert paths[0].exists()                     # the table was created


def test_create_and_read_round_trip(storage):
    ok, message = storage.save_all([make_record(1), make_record(2, "LOW", 10)])
    assert (ok, message) == (True, "")

    loaded = storage.load()
    assert [record.record_id for record in loaded] == [1, 2]
    assert loaded[0].indicators == ["Suspicious link", "Unexpected prize claim"]
    assert loaded[1].risk_level == "LOW"
    assert loaded[1].scam_probability == 10      # stays a number, not text


def test_update_changes_existing_row(storage, paths):
    record = make_record(1)
    storage.save_all([record])

    record.scam_type = "Phishing Scam"
    record.risk_level = "MEDIUM"
    storage.save_all([record])

    loaded = storage.load()
    assert count_rows(paths[0]) == 1             # updated, not duplicated
    assert loaded[0].scam_type == "Phishing Scam"
    assert loaded[0].risk_level == "MEDIUM"


def test_delete_removes_rows_missing_from_the_list(storage, paths):
    storage.save_all([make_record(1), make_record(2), make_record(3)])
    storage.save_all([make_record(1), make_record(3)])

    assert [record.record_id for record in storage.load()] == [1, 3]
    assert count_rows(paths[0]) == 2


def test_backup_is_updated_after_save(storage, paths):
    storage.save_all([make_record(1)])
    backup = json.loads(paths[1].read_text(encoding="utf-8"))
    assert [entry["record_id"] for entry in backup] == [1]


# ----------------------------------------------------------------------
# Failure cases
# ----------------------------------------------------------------------

def test_invalid_record_is_rejected_and_nothing_is_saved(storage, paths):
    storage.save_all([make_record(1)])
    bad = make_record(2, risk_level="EXTREME")

    ok, message = storage.save_all([make_record(1), bad])

    assert ok is False
    assert "risk_level" in message
    assert count_rows(paths[0]) == 1             # the database was not changed


def test_duplicate_ids_roll_back_the_whole_save(storage, paths):
    storage.save_all([make_record(1)])

    ok, message = storage.save_all([make_record(1), make_record(2), make_record(2)])

    assert ok is False
    assert "duplicate" in message.lower()
    assert [record.record_id for record in storage.load()] == [1]   # nothing half-saved


def test_empty_database_imports_records_from_backup(paths):
    """First run after switching from JSON: the backup file has the old records."""
    db_file, backup_file = paths
    old_entry = {
        "message_id": 7,                         # old Part 1 key still loads
        "timestamp": "2026-09-07 15:30:00",
        "phone_number": "+6591234567",
        "message_content": "Congratulations! Claim your prize now",
        "scam_probability": 96,
        "risk_level": "high",
        "scam_type": "Prize Scam",
        "indicators": ["Suspicious link"],
        "explanation": "Fake prize.",
        "recommendation": "Ignore it.",
    }
    backup_file.write_text(json.dumps([old_entry]), encoding="utf-8")

    storage = SqliteRecordStorage(str(db_file), str(backup_file))
    loaded = storage.load()

    assert [record.record_id for record in loaded] == [7]
    assert "Restored 1 record(s) from backup" in storage.status_message
    assert count_rows(db_file) == 1              # records are now in the database


def test_corrupt_database_is_preserved_and_rebuilt_from_backup(storage, paths):
    db_file, _backup_file = paths
    storage.save_all([make_record(1), make_record(2)])   # also writes the backup
    db_file.write_bytes(b"this is not an sqlite database at all" * 50)

    loaded = storage.load()

    assert [record.record_id for record in loaded] == [1, 2]
    assert "corrupt" in storage.status_message.lower()
    assert (db_file.parent / "scam_data.corrupt.db").exists()   # evidence kept
    assert count_rows(db_file) == 2                              # rebuilt


def test_database_that_cannot_be_opened_does_not_crash(tmp_path):
    folder_not_file = tmp_path / "scam_data.db"
    folder_not_file.mkdir()                      # SQLite cannot open a folder
    storage = SqliteRecordStorage(str(folder_not_file), str(tmp_path / "backup.json"))

    assert storage.load() == []
    assert "Could not open the database" in storage.status_message
    ok, message = storage.save_all([make_record(1)])
    assert ok is False
    assert "Could not write" in message


def test_row_with_broken_indicators_is_skipped(storage, paths):
    storage.save_all([make_record(1), make_record(2)])
    with closing(sqlite3.connect(paths[0])) as connection:
        with connection:
            connection.execute("UPDATE records SET indicators = 'not json' WHERE record_id = 2")

    loaded = storage.load()

    assert [record.record_id for record in loaded] == [1]
    assert storage.status_message == "Skipped 1 invalid record(s)."


# ----------------------------------------------------------------------
# DataManager works with SQLite without any change (polymorphism / LSP)
# ----------------------------------------------------------------------

def test_data_manager_full_crud_with_sqlite(paths):
    db_file, backup_file = paths
    manager = DataManager(SqliteRecordStorage(str(db_file), str(backup_file)))

    # Create
    assert manager.save_record(ai_output()) == (True, "")
    assert manager.save_record(ai_output()) == (True, "")
    # Read
    assert manager.find_record(2).scam_type == "Prize Scam"
    # Update
    assert manager.update_record(2, {"scam_type": "Phishing Scam"}) == (True, "")
    # Delete
    assert manager.remove_record(1) == (True, "")

    # A brand-new DataManager reads the same state back from the database
    reopened = DataManager(SqliteRecordStorage(str(db_file), str(backup_file)))
    assert [record.record_id for record in reopened.records] == [2]
    assert reopened.find_record(2).scam_type == "Phishing Scam"


def test_update_with_invalid_value_changes_nothing(paths):
    manager = DataManager(SqliteRecordStorage(*map(str, paths)))
    manager.save_record(ai_output())

    ok, message = manager.update_record(1, {"risk_level": "EXTREME"})

    assert ok is False
    assert "risk_level" in message
    assert manager.find_record(1).risk_level == "HIGH"


@pytest.mark.parametrize(
    "record_id, changes, expected_error",
    [
        (99, {"scam_type": "Phishing Scam"}, "No record with record_id 99."),
        (1, {"record_id": 5}, "record_id cannot be changed."),
        (1, {"colour": "red"}, "Unknown field: colour"),
        (1, {}, "No changes were given."),
    ],
)
def test_update_record_rejects_bad_requests(paths, record_id, changes, expected_error):
    manager = DataManager(SqliteRecordStorage(*map(str, paths)))
    manager.save_record(ai_output())

    assert manager.update_record(record_id, changes) == (False, expected_error)
