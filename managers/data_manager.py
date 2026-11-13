"""DataManager: holds the list of scam records and is what the app talks to (Phase 2b)."""
from storage.record_converter import RecordConverter
from storage.record_storage import RecordStorage
from storage.scam_statistics_calculator import ScamStatisticsCalculator
from models.record import Record


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
        print("Loading Database...")        
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

    def update_record(self, record_id: int, changes: dict) -> tuple[bool, str]:
        """Change some fields of an existing record and save the list.

        `changes` uses the JSON key names, e.g. {"scam_type": "Phishing Scam"}.
        The record_id itself cannot be changed. The changed record goes through
        the same RecordConverter checks as a new record.
        Returns (True, "") on success or (False, "reason").
        """
        record = self.find_record(record_id)
        if record is None:
            return False, f"No record with record_id {record_id}."
        if not isinstance(changes, dict) or not changes:
            return False, "No changes were given."

        updated_data = RecordConverter.to_dict(record)
        for key, value in changes.items():
            if key == "record_id":
                return False, "record_id cannot be changed."
            if key not in RecordConverter.SCHEMA:
                return False, f"Unknown field: {key}"
            updated_data[key] = value

        updated_record, error = RecordConverter.from_dict(updated_data)
        if updated_record is None:
            return False, error

        position = self._records.index(record)
        self._records[position] = updated_record
        ok, message = self._storage.save_all(self._records)
        if not ok:
            self._records[position] = record        # keep the list matching the storage
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