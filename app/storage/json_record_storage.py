# JsonRecordStorage: saves records to scam_data.json and backup_database.json acts as a fallback.

import json

from app.storage.backup_database import BackupDatabase
from app.storage.record_converter import RecordConverter
from app.interfaces.record_storage import RecordStorage
from app.storage.safe_json_file import SafeJsonFile
from app.models.record import Record


class JsonRecordStorage(RecordStorage):
    """a RecordStorage that uses JSON files. Creates and owns its SafeJsonFile and BackupDatabase."""

    def __init__(self, data_file: str = "./data/scam_data.json", backup_file: str = "./data/backup_database.json",) -> None:
        # Create the main file and backup.
        super().__init__()          # sets up status_message from RecordStorage

        self._main_file = SafeJsonFile(data_file)
        self._backup = BackupDatabase(backup_file)

    # ------------------------------------------------------------------
    # Public methods (what DataManager is allowed to call)
    # ------------------------------------------------------------------

    def load(self) -> list[Record]:
        """Load all valid records from the main file.

        If the main file is missing, empty, corrupt or in the wrong format,
        records are recovered from the backup instead.
        """
        # A 0-byte file is empty, not corrupt (fix from the Phase 1 review).
        if self._main_file.is_empty():
            return self._recover_from_backup("Main data file was empty.")

        try:
            data = self._main_file.read()
        except FileNotFoundError:
            return self._recover_from_backup("Main data file was missing.")
        except (json.JSONDecodeError, UnicodeDecodeError):
            preserved = self._backup.preserve_corrupt(self._main_file.path)
            if preserved:
                reason = f"Main data file was corrupt. Retrieving from Backup."
            else:
                reason = "Main data file was corrupt; could not preserve its contents."
            return self._recover_from_backup(reason)
        except OSError:
            return self._recover_from_backup("Could not read the main data file.")

        if not isinstance(data, list):
            preserved = self._backup.preserve_corrupt(self._main_file.path)
            if preserved:
                reason = f"Main data file had the wrong format. Retrieving from Backup."
            else:
                reason = "Main data file had the wrong format."
            return self._recover_from_backup(reason)

        if not data:
            return self._recover_from_backup("Main data file was empty.")

        records, skipped = RecordConverter.from_list(data)
        if skipped > 0:
            self._status_message = f"Skipped {skipped} invalid record(s)."
        else:
            self._status_message = ""
        return records

    def save_all(self, records: list[Record]) -> tuple[bool, str]:
        """Validate and save to the main file then update the backup."""
        for record in records:
            is_valid, error = RecordConverter.check_record(record)
            if not is_valid:
                return False, error

        try:
            self._main_file.write([RecordConverter.to_dict(saved) for saved in records])
        except (OSError, TypeError, ValueError):
            return False, "Could not write to the data file."

        # The backup is only updated after the main file was saved.
        if not self._backup.update(records):
            return (
                True,
                "Records saved, but the backup database could not be updated. "
                "The previous backup was preserved where possible.",
            )

        return True, ""

    # ------------------------------------------------------------------
    # Private helper (only used inside this class)
    # ------------------------------------------------------------------

    def _recover_from_backup(self, reason: str) -> list[Record]:
        """Restore the main file with records from the backup and set the status message."""
        backup_records = self._backup.load_valid_records()

        if not backup_records:
            self._status_message = f"{reason} No valid backup records were available."
            return []

        try:
            self._main_file.write(
                [RecordConverter.to_dict(record) for record in backup_records]
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