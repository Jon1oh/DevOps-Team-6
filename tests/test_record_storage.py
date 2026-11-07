"""Tests for RecordStorage and its two child classes. Run with:

    python -m pytest tests/test_record_storage.py

The tests marked "both storages" run TWICE: once with JsonRecordStorage and
once with TemporaryRecordStorage. Passing both times is the evidence for
polymorphism and LSP (either child can replace the other).
"""

import pytest

from classes.json_record_storage import JsonRecordStorage
from classes.record_storage import RecordStorage
from classes.record_converter import RecordConverter
from record import Record
from classes.temp_record_storage import TemporaryRecordStorage
from managers.data_manager import DataManager


def make_record(record_id: int = 1) -> Record:
    record, _error = RecordConverter.from_dict({
        "record_id": record_id,
        "timestamp": "2026-10-02 11:40:00",
        "phone_number": "+6591234567",
        "country_code": "+65",
        "message_content": "Your account is suspended. Click http://bad.link",
        "scam_probability": 90,
        "risk_level": "HIGH",
        "scam_type": "Bank Impersonation Scam",
        "indicators": ["Urgent language"],
        "explanation": "Impersonates a bank.",
        "recommendation": "Do not click the link.",
    })
    return record


@pytest.fixture(params=["json", "temporary"])
def storage(request, tmp_path) -> RecordStorage:
    """Gives each test a storage object, once for each kind of storage."""
    if request.param == "json":
        return JsonRecordStorage(
            data_file=str(tmp_path / "scam_data.json"),
            backup_file=str(tmp_path / "backup_database.json"),
        )
    return TemporaryRecordStorage()


# ---------- abstract class and inheritance ----------

def test_abstract_class_cannot_be_created() -> None:
    with pytest.raises(TypeError):
        RecordStorage()


def test_child_missing_a_method_cannot_be_created() -> None:
    class BrokenStorage(RecordStorage):
        def load(self):          # save() is missing on purpose
            return []

    with pytest.raises(TypeError):
        BrokenStorage()


def test_both_children_are_record_storages() -> None:
    assert issubclass(JsonRecordStorage, RecordStorage)
    assert issubclass(TemporaryRecordStorage, RecordStorage)


# ---------- both storages: same behaviour (polymorphism / LSP) ----------

def test_starts_empty(storage) -> None:
    assert storage.load() == []
    assert storage.next_id() == 1


def test_save_then_load(storage) -> None:
    assert storage.save(make_record()) == (True, "")
    records = storage.load()
    assert len(records) == 1
    assert isinstance(records[0], Record)


def test_next_id_is_highest_plus_one(storage) -> None:
    storage.save(make_record(3))
    storage.save(make_record(7))
    assert storage.next_id() == 8


def test_rejects_non_record(storage) -> None:
    assert storage.save({"not": "a record"}) == (
        False, "Only Record objects can be saved.")


def test_rejects_unfinished_record(storage) -> None:
    # Record() with its default values has no message and no valid risk level.
    ok, _error = storage.save(Record())
    assert ok is False
    assert storage.load() == []


def test_status_message_is_read_only(storage) -> None:
    with pytest.raises(AttributeError):
        storage.status_message = "hacked"


def test_data_manager_works_with_any_storage(storage) -> None:
    manager = DataManager(storage)       # no type checks inside DataManager
    data = RecordConverter.to_dict(make_record())

    assert manager.save_record(data) == (True, "")
    assert manager.save_record(data) == (True, "")
    assert [record.record_id for record in manager.load_records()] == [1, 2]
    assert manager.summary()["total_messages"] == 2


# ---------- temporary storage only ----------

def test_temporary_storage_list_cannot_be_changed_from_outside() -> None:
    storage = TemporaryRecordStorage()
    storage.save(make_record())
    storage.load().clear()               # changes a copy only
    assert len(storage.load()) == 1