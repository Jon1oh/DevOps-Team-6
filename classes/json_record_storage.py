"""JsonRecordStorage: saves and loads ScamRecords in a JSON file."""

import json
import os
import tempfile

from classes.scam_record import ScamRecord

class JsonRecordStorage:
    """Stores ScamRecord objects in scam_data.json, with a backup file.

    - load() returns the saved records and never crashes.
    - save() adds one record, writing the main file first and then the backup.
    - status_message tells io_manager what happened during the last load,
      e.g. "Skipped 2 invalid record(s)." ("" means everything was normal).
    """

    def __init__(
        self,
        data_file: str = "./data/scam_data.json",
        backup_file: str = "./data/backup_database.json",
    ) -> None:
        self._data_file = data_file
        self._backup_file = backup_file
        self._status_message = ""

    @property
    def status_message(self) -> str:
        """Read-only: there is a getter but no setter, so outside code
        cannot change it."""
        return self._status_message


    def load(self) -> list[ScamRecord]:
        """Load all valid records from the main file.

        If the main file is missing, empty, corrupt or in the wrong format,
        records are recovered from the backup instead.
        """
        if os.path.exists(self._data_file) and os.path.getsize(self._data_file) == 0:
            return self._recover_from_backup("Main data file was empty.")

        try:
            with open(self._data_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return self._recover_from_backup("Main data file was missing.")
        except (json.JSONDecodeError, UnicodeDecodeError):
            preserved = self._preserve_corrupt_file()
            if preserved:
                reason = f"Data file was corrupt. Preserved at {preserved}."
            else:
                reason = "Data file was corrupt; could not preserve its contents."
            return self._recover_from_backup(reason)
        except OSError:
            return self._recover_from_backup("Could not read the main data file.")        

        if not isinstance(data, list):
            preserved = self._preserve_corrupt_file()
            if preserved:
                reason = f"Data file had the wrong format. Preserved at {preserved}."
            else:
                reason = "Data file had the wrong format."
            return self._recover_from_backup(reason)

        if not data:
            return self._recover_from_backup("Main data file was empty.")

        records, skipped = self._convert_entries(data)
        if skipped > 0:
            self._status_message = f"Skipped {skipped} invalid record(s)."
        else:
            self._status_message = ""
        return records

    def save(self, record: ScamRecord) -> tuple[bool, str]:
        """Add one record. Writes the main file, then the backup.

        Returns (True, "") on success, (True, "warning") if only the backup
        failed, or (False, "reason") if the record could not be saved.
        """

        if not isinstance(record, ScamRecord):
            return False, "Only ScamRecord objects can be saved."

        records = self.load()
        records.append(record)
        entries = [saved.to_dict() for saved in records]

        try:
            self._write_json_atomically(self._data_file, entries)
        except (OSError, TypeError, ValueError):
            return False, "Could not write to the data file."

        # The backup is only updated after the main file was saved.
        try:
            self._write_json_atomically(self._backup_file, entries)
        except (OSError, TypeError, ValueError):
            return (
                True,
                "Record saved, but the backup database could not be updated. "
                "The previous backup was preserved where possible.",
            )

        return True, ""

    def next_id(self) -> int:
        """Return the next free message_id: highest saved id + 1, or 1 if none."""
        highest = 0
        for record in self.load():
            if record.message_id > highest:
                highest = record.message_id
        return highest + 1

    @staticmethod
    def _convert_entries(entries: list) -> tuple[list[ScamRecord], int]:
        """Turn raw JSON entries into ScamRecords. Returns (records, skipped_count)."""
        records = []
        skipped = 0
        for entry in entries:
            record, _error = ScamRecord.from_dict(entry)
            if record is None:
                skipped += 1
            else:
                records.append(record)
        return records, skipped    

    def _load_backup_records(self) -> list[ScamRecord]:
        """Load only the valid records from the backup file ([] if unusable)."""
        try:
            with open(self._backup_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []

        if not isinstance(data, list):
            return []

        records, _skipped = self._convert_entries(data)
        return records

    def _recover_from_backup(self, reason: str) -> list[ScamRecord]:
        """Restore the main file from the backup and set the status message."""
        backup_records = self._load_backup_records()

        if not backup_records:
            self._status_message = f"{reason} No valid backup records were available."
            return []

        try:
            self._write_json_atomically(
                self._data_file, [record.to_dict() for record in backup_records]
            )
        except (OSError, TypeError, ValueError):
            # The records are still usable even though the file was not restored.
            self._status_message = (
                f"{reason} Recovered records in memory, but could not "
                "restore the main data file."
            )
            return backup_records

        self._status_message = (
            f"{reason} Restored {len(backup_records)} record(s) from backup."
        )
        return backup_records

    def _preserve_corrupt_file(self) -> str:
        """Rename a corrupt main file to .corrupt.json. Returns the new name, or ""."""
        preserved_name = self._data_file.replace(".json", ".corrupt.json")
        try:
            os.replace(self._data_file, preserved_name)
        except OSError:
            return ""
        return preserved_name

    @staticmethod
    def _write_json_atomically(file_path: str, entries: list[dict]) -> None:
        """Write to a temporary file first, then swap it in with os.replace().

        If the program crashes while writing, the original file is untouched.
        """
        directory = os.path.dirname(os.path.abspath(file_path))
        os.makedirs(directory, exist_ok=True)
        temp_path = ""

        try:
            file_descriptor, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(entries, file, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, file_path)
            temp_path = ""
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)