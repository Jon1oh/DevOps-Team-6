# DataManager: keeps the scam records in memory and saves every change through a storage
from app.storage.record_converter import RecordConverter
from app.interfaces.record_storage import RecordStorage
from app.storage.scam_statistics_calculator import ScamStatisticsCalculator
from app.models.record import Record


class DataManager:
    """Holds the list of Record objects that the rest of the app uses

    - The list is loaded once from the storage when DataManager is created,
      and every method works on that list.
    - After every change, the whole list is written back through the storage

    The storage is given to DataManager through the constructor.
    """

    def __init__(self, storage: RecordStorage) -> None:
        """Load all records once from the given storage."""
        self._storage: RecordStorage = storage
        # The main list of records: loaded once, then kept in memory.
        self._records: list[Record] = storage.load()

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @property
    def records(self) -> list[Record]:
        """Return a copy of the records"""
        return list(self._records)

    @property
    def status_message(self) -> str:
        """Return what happened when the records were loaded,
        e.g. "Skipped 2 invalid record(s)." ("" means everything was normal)."""
        return self._storage.status_message

    def find_record(self, record_id: int) -> Record | None:
        """Return the record with this record_id, or None."""
        for record in self._records:
            if record.record_id == record_id:
                return record
        return None

    def next_id(self) -> int:
        """Return the next free record_id: highest id in the list + 1, or 1 if list empty."""
        highest = 0
        for record in self._records:
            if record.record_id > highest:
                highest = record.record_id
        return highest + 1

    def count_risk_levels(self, phone_number: str) -> dict[str, int]:
        """Count past HIGH/MEDIUM/LOW results for one phone number."""
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for record in self._records:
            if record.phone_number == phone_number:
                counts[record.risk_level] += 1
        return counts

    def summary(self, records: list[Record] | None = None) -> dict:
        """Return the summary statistics"""
        if records is None:
            records = self._records
        return ScamStatisticsCalculator().summary(records)

    # ------------------------------------------------------------------
    # Updating the list (each change is saved straight away)
    # ------------------------------------------------------------------

    def save_record(self, data: dict) -> tuple[bool, str]:
        """Turn a dictionary (the final AI output) into a Record, add it
        to the list and save the list.

        The record always gets the next free id
        """
        if not isinstance(data, dict):
            return False, "Record is not a dictionary."

        new_data = dict(data)                      # never change the caller's dict
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
        """Remove the record and save the list.

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