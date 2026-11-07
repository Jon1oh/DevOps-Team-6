"""Tests for classes/safe_json_file.py. Run from the project folder with:

    python -m pytest tests/test_safe_json_file.py
"""

import json
import os

import pytest

from classes.json_record_storage import JsonRecordStorage
from classes.safe_json_file import SafeJsonFile


# ---------- reading ----------

def test_write_then_read(tmp_path) -> None:
    file = SafeJsonFile(str(tmp_path / "data.json"))
    file.write([{"a": 1}, {"b": 2}])
    assert file.read() == [{"a": 1}, {"b": 2}]


def test_missing_file_raises_file_not_found(tmp_path) -> None:
    file = SafeJsonFile(str(tmp_path / "missing.json"))
    with pytest.raises(FileNotFoundError):
        file.read()


def test_corrupt_file_raises_decode_error(tmp_path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        SafeJsonFile(str(path)).read()


def test_is_empty(tmp_path) -> None:
    path = tmp_path / "data.json"
    file = SafeJsonFile(str(path))

    assert file.is_empty() is False        # does not exist yet
    path.write_text("", encoding="utf-8")
    assert file.is_empty() is True         # exists, 0 bytes
    file.write([])
    assert file.is_empty() is False        # contains "[]"


# ---------- writing ----------

def test_write_creates_missing_folder(tmp_path) -> None:
    file = SafeJsonFile(str(tmp_path / "new_folder" / "data.json"))
    file.write([1, 2, 3])
    assert file.read() == [1, 2, 3]


def test_write_replaces_old_content(tmp_path) -> None:
    file = SafeJsonFile(str(tmp_path / "data.json"))
    file.write(["old"])
    file.write(["new"])
    assert file.read() == ["new"]


def test_failed_write_keeps_original_and_leaves_no_temp_file(tmp_path) -> None:
    file = SafeJsonFile(str(tmp_path / "data.json"))
    file.write(["original"])

    with pytest.raises(TypeError):
        file.write([object()])             # an object cannot be turned into JSON

    assert file.read() == ["original"]     # old file untouched
    assert [name for name in os.listdir(tmp_path) if name.endswith(".tmp")] == []


def test_path_is_read_only(tmp_path) -> None:
    file = SafeJsonFile(str(tmp_path / "data.json"))
    with pytest.raises(AttributeError):
        file.path = "somewhere_else.json"


# ---------- composition ----------

def test_json_storage_creates_its_own_safe_json_files(tmp_path) -> None:
    storage = JsonRecordStorage(
        data_file=str(tmp_path / "scam_data.json"),
        backup_file=str(tmp_path / "backup_database.json"),
    )
    # Each storage object builds its own SafeJsonFile objects inside __init__.
    assert isinstance(storage._main_file, SafeJsonFile)
    assert isinstance(storage._backup_file, SafeJsonFile)