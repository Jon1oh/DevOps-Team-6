"""RecordStorage: the abstract parent class for every kind of record storage (Phase 2b)."""

from abc import ABC, abstractmethod

from app.models.record import Record


class RecordStorage(ABC):
    """Describes what every storage must be able to do, without saying how.

    - load() and save_all() are ABSTRACT: each child class must write its own.
    - status_message is CONCRETE: shared by every child, written once here
      (inheritance means the children get it for free).

    A storage only reads and writes the WHOLE list of records. Keeping the
    list in memory and changing it is DataManager's job.

    RecordStorage itself cannot be created: RecordStorage() raises TypeError.
    """

    def __init__(self) -> None:
        self._status_message: str = ""

    @property
    def status_message(self) -> str:
        """What happened during the last load ("" means everything was normal)."""
        return self._status_message

    @abstractmethod
    def load(self) -> list[Record]:
        """Return every saved record. Must never crash."""

    @abstractmethod
    def save_all(self, records: list[Record]) -> tuple[bool, str]:
        """Replace everything stored with `records`.

        Return (True, "") on success, (True, "warning") if the records were
        saved with a problem worth reporting, or (False, "reason") if nothing
        was saved.
        """