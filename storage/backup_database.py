import json
import os

from storage.record_converter import RecordConverter
from storage.safe_json_file import SafeJsonFile
from app.models.record import Record

class BackupDatabase:
    """keeps the backup copy of the main database"""
    def __init__(self, backup_path: str) -> None:
        self._file = SafeJsonFile(backup_path)

    @property
    def path(self) -> str:
        """The path for backup file"""
        return self._file.path

    def update(self, records: list[Record]) -> bool:
        """Replace the backup with `records`. Returns True if it worked.
 
        The write is atomic.
        """
        entries = [RecordConverter.to_dict(record) for record in records]
        try:
            self._file.write(entries)
        except (OSError, TypeError, ValueError):
            return False
        return True

    def load_valid_records(self) -> list[Record]:
        """Returns [] and gracefully handles when the backup is corrupt, missing or unreadable"""
        try:
            data = self._file.read()
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []
 
        if not isinstance(data, list):
            return []
 
        records, _skipped = RecordConverter.from_list(data)
        return records        

    @staticmethod
    def preserve_corrupt(file_path: str) -> str:
        """Rename a corrupt file to *.corrupt.json so its contents are not lost.
 
        e.g. scam_data.json -> scam_data.corrupt.json
        Returns the new name, or "" if the rename failed.
        """
        preserved_name = file_path.replace(".json", ".corrupt.json")
        try:
            os.replace(file_path, preserved_name)
        except OSError:
            return ""
        return preserved_name