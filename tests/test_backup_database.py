"""Tests for classes/backup_database.py. Run from the project folder with:

    python -m pytest tests/test_backup_database.py
"""

import json
import os

from classes.backup_database import BackupDatabase
from classes.json_record_storage import JsonRecordStorage
from classes.record_converter import RecordConverter
from classes.safe_json_file import SafeJsonFile


def make_valid_dict(record_id: int = 1, risk_level: str = "HIGH") -> dict:
    return {
        "record_id": record_id,
        "timestamp": "2026-10-02 11:40:00",
        "phone_number": "+6591234567",
        "country_code": "+65",
        "message_content": "Your account is suspended. Click http://bad.link",
        "scam_probability": 90,
        "risk_level": risk_level,
        "scam_type": "Bank Impersonation Scam",
        "indicators": ["Urgent language"],
        "explanation": "Impersonates a bank.",
        "recommendation": "Do not click the link.",
    }


def make_backup(tmp_path) -> BackupDatabase:
    return BackupDatabase(str(tmp_path / "backup_database.json"))


# ---------- update ----------

def test_update_then_load(tmp_path) -> None:
    backup = make_backup(tmp_path)
    record, _error = RecordConverter.from_dict(make_valid_dict())

    assert backup.update([record]) is True

    loaded = backup.load_valid_records()
    assert len(loaded) == 1
    assert loaded[0].record_id == 1


def test_update_failure_returns_false(tmp_path) -> None:
    os.makedirs(tmp_path / "backup_database.json")   # a folder blocks the file
    record, _error = RecordConverter.from_dict(make_valid_dict())
    assert make_backup(tmp_path).update([record]) is False


# ---------- loading for recovery ----------

def test_missing_backup_gives_empty_list(tmp_path) -> None:
    assert make_backup(tmp_path).load_valid_records() == []


def test_corrupt_backup_gives_empty_list(tmp_path) -> None:
    (tmp_path / "backup_database.json").write_text("{ broken", encoding="utf-8")
    assert make_backup(tmp_path).load_valid_records() == []


def test_non_list_backup_gives_empty_list(tmp_path) -> None:
    (tmp_path / "backup_database.json").write_text('{"a": 1}', encoding="utf-8")
    assert make_backup(tmp_path).load_valid_records() == []


def test_only_valid_backup_records_are_returned(tmp_path) -> None:
    entries = [make_valid_dict(1), make_valid_dict(2, risk_level="UNKNOWN"), "garbage"]
    (tmp_path / "backup_database.json").write_text(json.dumps(entries), encoding="utf-8")

    loaded = make_backup(tmp_path).load_valid_records()

    assert [record.record_id for record in loaded] == [1]


# ---------- preserving a corrupt main file ----------

def test_preserve_corrupt_renames_file(tmp_path) -> None:
    main = tmp_path / "scam_data.json"
    main.write_text("{ broken", encoding="utf-8")

    preserved = BackupDatabase.preserve_corrupt(str(main))

    assert preserved.endswith("scam_data.corrupt.json")
    assert os.path.exists(preserved)
    assert not os.path.exists(main)


def test_preserve_missing_file_returns_empty_string(tmp_path) -> None:
    assert BackupDatabase.preserve_corrupt(str(tmp_path / "nothing.json")) == ""


# ---------- composition ----------

def test_backup_creates_its_own_safe_json_file(tmp_path) -> None:
    backup = make_backup(tmp_path)
    assert isinstance(backup._file, SafeJsonFile)


def test_json_storage_creates_its_own_backup_database(tmp_path) -> None:
    storage = JsonRecordStorage(
        data_file=str(tmp_path / "scam_data.json"),
        backup_file=str(tmp_path / "backup_database.json"),
    )
    assert isinstance(storage._backup, BackupDatabase)