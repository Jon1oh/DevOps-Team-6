"""DataManager: the one class the rest of the app talks to for saved records (Phase 2b)."""

from classes.json_record_storage import JsonRecordStorage
from classes.record_converter import RecordConverter
from classes.record_storage import RecordStorage
from classes.scam_statistics_calculator import ScamStatisticsCalculator
from record import Record


class DataManager:
    """Coordinates saving, loading and summarising scam records.

    It does not read or write files itself. It is given a storage object
    in its constructor and asks that object to do the work
    (aggregation: the storage exists outside DataManager and is passed in).

    The storage can be ANY RecordStorage child (JsonRecordStorage,
    TemporaryRecordStorage, ...). DataManager never checks which one it got
    (polymorphism), so a new storage class needs no change here (OCP).
    """

    def __init__(self, storage: RecordStorage) -> None:
        self._storage = storage

    @property
    def status_message(self) -> str:
        """What happened during the last load, e.g. "Skipped 2 invalid record(s)."."""
        return self._storage.status_message

    def load_records(self) -> list[Record]:
        """Return every saved record as a Record object."""
        return self._storage.load()

    def get_record(self, record_id: int) -> Record | None:
        """Return the record with this record_id, or None if there is none."""
        for record in self._storage.load():
            if record.record_id == record_id:
                return record
        return None

    def save_record(self, data: dict) -> tuple[bool, str]:
        """Turn a dictionary (e.g. the final AI output) into a Record and save it.

        The record always gets the next free id; any id in `data` is ignored,
        so ids never repeat. Returns (ok, message).
        """
        if not isinstance(data, dict):
            return False, "Record is not a dictionary."

        new_data = dict(data)                      # never change the caller's dict
        new_data.pop("message_id", None)           # old name: never trust it either
        new_data["record_id"] = self._storage.next_id()

        record, error = RecordConverter.from_dict(new_data)
        if record is None:
            return False, error

        return self._storage.save(record)

    def count_risk_levels(self, phone_number: str) -> dict[str, int]:
        """Count past HIGH/MEDIUM/LOW results for one phone number.

        e.g. {"HIGH": 2, "MEDIUM": 0, "LOW": 1}
        """
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for record in self._storage.load():
            if record.phone_number == phone_number:
                counts[record.risk_level] += 1
        return counts

    def summary(self, records: list[Record] | None = None) -> dict:
        """Return the summary dictionary for io_manager.print_message_summary().

        Uses the saved records unless a list is passed in.
        The calculator is created only when needed, so DataManager does not
        own it (association, not composition).
        """
        if records is None:
            records = self._storage.load()
        return ScamStatisticsCalculator().summary(records)


# =====================================================================
# TEMPORARY wrappers so app.py keeps working without being edited.
# app.py calls these four module-level functions, exactly as in Phase 1.
# REMOVE this whole section before submission, once app.py creates and
# uses a DataManager object directly.
# =====================================================================

_default_manager = DataManager(JsonRecordStorage())


def load_records() -> list[dict]:
    """Phase 1 style: return records as plain dictionaries.

    Each dictionary also gets the old key "message_id", in case io_manager
    or app.py still reads it. Delete that line once nothing uses message_id.
    """
    entries = []
    for record in _default_manager.load_records():
        entry = RecordConverter.to_dict(record)
        entry["message_id"] = entry["record_id"]    # TEMPORARY old name
        entries.append(entry)
    return entries


def save_record(record: dict) -> tuple[bool, str]:
    return _default_manager.save_record(record)


def count_risk_levels(phone_number: str) -> dict[str, int]:
    return _default_manager.count_risk_levels(phone_number)


def summary_with_percentages(records: list) -> dict:
    """Phase 1 style: accepts the dictionaries that load_records() returned."""
    converted = []
    for entry in records:
        if isinstance(entry, Record):
            converted.append(entry)
        else:
            record, _error = RecordConverter.from_dict(entry)
            if record is not None:
                converted.append(record)
    return _default_manager.summary(converted)