# RecordStorage: the abstract parent class for every kind of record storage.

from abc import ABC, abstractmethod

from app.models.record import Record


class RecordStorage(ABC):
    """Describes what every storage must be able to do, without saying how.

    - load() and save_all() are abstract
    - status_message is shared code that every child inherits
    """

    def __init__(self) -> None:
        """Start with no status message."""
        self._status_message: str = ""

    @property
    def status_message(self) -> str:
        """What happened during the last load ("" means everything was normal)."""
        return self._status_message

    @abstractmethod
    def load(self) -> list[Record]:
        """Return every saved record."""

    @abstractmethod
    def save_all(self, records: list[Record]) -> tuple[bool, str]:
        """Replace all saved records. Return (True, "") on success, (True, "warning") if the records were
        saved with a problem worth reporting, or (False, "reason") if nothing was saved.
        """