"""RecordStorage: the abstract parent class for every kind of record storage (Phase 2b)."""

from abc import ABC, abstractmethod

from record import Record


class RecordStorage(ABC):
    """Describes what every storage must be able to do, without saying how.

    - load() and save() are ABSTRACT: each child class must write its own.
    - next_id() and status_message are CONCRETE: shared by every child,
      written once here (inheritance means the children get them for free).

    RecordStorage itself cannot be created: RecordStorage() raises TypeError.
    """

    def __init__(self) -> None:
        self._status_message = ""

    @property
    def status_message(self) -> str:
        """What happened during the last load ("" means everything was normal)."""
        return self._status_message

    @abstractmethod
    def load(self) -> list[Record]:
        """Return every saved record. Must never crash."""

    @abstractmethod
    def save(self, record: Record) -> tuple[bool, str]:
        """Add one record. Return (True, "") on success or (False, "reason")."""

    def next_id(self) -> int:
        """Return the next free record_id: highest saved id + 1, or 1 if none.

        It calls self.load(), so it works for ANY child class: Python runs the
        child's own load() (polymorphism).
        """
        highest = 0
        for record in self.load():
            if record.record_id > highest:
                highest = record.record_id
        return highest + 1