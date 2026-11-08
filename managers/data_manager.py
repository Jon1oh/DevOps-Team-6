"""DataManager: holds the list of scam records and is what the app talks to (Phase 2b)."""

from models.json_record_storage import JsonRecordStorage
from models.record_converter import RecordConverter
from models.record_storage import RecordStorage
from models.scam_statistics_calculator import ScamStatisticsCalculator
from record import Record


class DataManager:
    """Keeps the main list of Record objects, like Inventory keeps its products.

    - The list is loaded ONCE from the storage when DataManager is created,
      and every method works on that list.
    - After every change, the whole list is written back through the storage,
      so the list and the file always match.

    The storage is given to DataManager through the constructor
    (aggregation): it can be ANY RecordStorage child (JsonRecordStorage,
    TemporaryRecordStorage, ...), and DataManager never checks which one it got
    (polymorphism), so a new storage class needs no change here (OCP).
    """

    def __init__(self, storage: RecordStorage) -> None:
        self._storage: RecordStorage = storage
        # The main list of records: loaded once, then kept in memory.
        self._records: list[Record] = storage.load()

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @property
    def records(self) -> list[Record]:
        """Every record in memory. A copy of the list is returned, so outside
        code cannot add or remove records without going through DataManager."""
        return list(self._records)

    @property
    def status_message(self) -> str:
        """What happened when the records were loaded,
        e.g. "Skipped 2 invalid record(s)." ("" means everything was normal)."""
        return self._storage.status_message

    def find_record(self, record_id: int) -> Record | None:
        """Return the record with this record_id, or None if there is none."""
        for record in self._records:
            if record.record_id == record_id:
                return record
        return None

    def next_id(self) -> int:
        """Return the next free record_id: highest id in the list + 1, or 1 if empty."""
        highest = 0
        for record in self._records:
            if record.record_id > highest:
                highest = record.record_id
        return highest + 1

    def count_risk_levels(self, phone_number: str) -> dict[str, int]:
        """Count past HIGH/MEDIUM/LOW results for one phone number.

        e.g. {"HIGH": 2, "MEDIUM": 0, "LOW": 1}
        """
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for record in self._records:
            if record.phone_number == phone_number:
                counts[record.risk_level] += 1
        return counts

    def summary(self, records: list[Record] | None = None) -> dict:
        """Return the summary dictionary for io_manager.print_message_summary().

        Uses the records in memory unless a list is passed in.
        The calculator is created only when needed and not kept, so
        DataManager does not own it (association, not composition).
        """
        if records is None:
            records = self._records
        return ScamStatisticsCalculator().summary(records)

    # ------------------------------------------------------------------
    # Changing the list (each change is saved straight away)
    # ------------------------------------------------------------------

    def save_record(self, data: dict) -> tuple[bool, str]:
        """Turn a dictionary (e.g. the final AI output) into a Record, add it
        to the list and save the list.

        The record always gets the next free id; any id in `data` is ignored,
        so ids never repeat. Returns (ok, message).
        """
        if not isinstance(data, dict):
            return False, "Record is not a dictionary."

        new_data = dict(data)                      # never change the caller's dict
        new_data.pop("message_id", None)           # old name: never trust it either
        new_data["record_id"] = self.next_id()

        record, error = RecordConverter.from_dict(new_data)
        if record is None:
            return False, error

        self._records.append(record)
        ok, message = self._storage.save_all(self._records)
        if not ok:
            self._records.remove(record)           # keep the list matching the file
        return ok, message

    def remove_record(self, record_id: int) -> tuple[bool, str]:
        """Remove the record with this record_id from the list and save the list.

        Returns (True, "") on success or (False, "reason").
        """
        record = self.find_record(record_id)
        if record is None:
            return False, f"No record with record_id {record_id}."

        position = self._records.index(record)
        self._records.remove(record)
        ok, message = self._storage.save_all(self._records)
        if not ok:
            self._records.insert(position, record)  # put it back where it was
        return ok, message


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
    for record in _default_manager.records:
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