"""SafeJsonFile: reads and writes ONE JSON file safely (Phase 2b)."""

import json
import os
import tempfile

class SafeJsonFile:
    """Writes file Atomically by writing to temporary file first then swapping it after it is successfully written
    
    It knows nothing about scam records: it just stores lists and dictionaries.
    """
    def __init__(self, path: str) -> None:
        self._path = path

    @property
    def path(self) -> str:
        """For the file's location (read-only)"""
        return self._path

    def is_empty(self) -> bool:
        """Check if the existing file is empty"""
        return os.path.exists(self._path) and os.path.getsize(self._path) == 0

    def read(self) -> object:
        """Return the parsed JSON content of the file"""
        with open(self._path, "r", encoding="utf-8") as file:
            return json.load(file)   
         
    def write(self, entries: list) -> None:
        """Replace the file's content atomically.

        the original file is left untouched if there is an error if the write fails.
        """
        directory = os.path.dirname(os.path.abspath(self._path))
        os.makedirs(directory, exist_ok=True)
        temp_path = ""

        try:
            file_descriptor, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(entries, file, indent=4)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, self._path)
            temp_path = ""          # nothing left to clean up
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)