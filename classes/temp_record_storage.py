"""TemporaryRecordStorage: keeps records in memory only (Phase 2b)."""

from classes.record_converter import RecordConverter
from classes.record_storage import RecordStorage
from record import Record


class TemporaryRecordStorage(RecordStorage):
    """Stores records in a private Python list. Nothing is written to disk,
    so the records disappear when the program ends.

    Used for fast tests and to prove DataManager works with any storage.
    It returns exactly the same shapes as JsonRecordStorage (LSP).
    """

    def __init__(self) -> None:
        super().__init__()          # sets up status_message from the parent
        self._records: list[Record] = []

    def load(self) -> list[Record]:
        # Return a copy of the list, so callers cannot change our list directly.
        return list(self._records)

    def save(self, record: Record) -> tuple[bool, str]:
        is_valid, error = RecordConverter.check_record(record)
        if not is_valid:
            return False, error
        self._records.append(record)
        return True, ""