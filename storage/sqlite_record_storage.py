"""SqliteRecordStorage: saves and loads Records in an SQLite database (Phase 2 advanced feature).

It is a third child of RecordStorage, next to JsonRecordStorage, so DataManager
can use it without any change (polymorphism, OCP, LSP).

It creates one helper object for itself (composition):
- a BackupDatabase that keeps backup_database.json up to date after every
  successful save, and is used to rebuild the database if it is lost or corrupt.
"""

import json
import os
import sqlite3
from contextlib import closing

from models.record import Record
from storage.backup_database import BackupDatabase
from storage.record_converter import RecordConverter
from storage.record_storage import RecordStorage


class SqliteRecordStorage(RecordStorage):
    """Stores Record objects in the `records` table of an SQLite database.

    - load() reads every row (SELECT) and never crashes.
    - save_all() makes the table match the list using INSERT, UPDATE and DELETE
      inside ONE transaction: either every change is saved, or none is.
    - status_message tells io_manager what happened during the last load.

    Row and column names match the JSON key names in RecordConverter, so the
    same validation rules are used for both storages.
    """

    # Column order used for INSERT and SELECT (same names as the JSON keys).
    COLUMNS = (
        "record_id",
        "timestamp",
        "phone_number",
        "country_code",
        "message_content",
        "scam_probability",
        "risk_level",
        "scam_type",
        "indicators",
        "explanation",
        "recommendation",
    )

    _CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS records (
            record_id        INTEGER PRIMARY KEY,
            timestamp        TEXT    NOT NULL,
            phone_number     TEXT    NOT NULL,
            country_code     TEXT    NOT NULL,
            message_content  TEXT    NOT NULL,
            scam_probability NUMERIC NOT NULL
                             CHECK (scam_probability BETWEEN 0 AND 100),
            risk_level       TEXT    NOT NULL
                             CHECK (risk_level IN ('HIGH', 'MEDIUM', 'LOW')),
            scam_type        TEXT    NOT NULL,
            indicators       TEXT    NOT NULL,  -- list stored as JSON text
            explanation      TEXT    NOT NULL,
            recommendation   TEXT    NOT NULL
        )
    """

    def __init__(
        self,
        db_file: str = "./data/scam_data.db",
        backup_file: str = "./data/backup_database.json",
    ) -> None:
        super().__init__()          # sets up status_message from RecordStorage
        self._db_path = db_file
        # Composition: this storage CREATES and OWNS its backup helper.
        self._backup = BackupDatabase(backup_file)

    @property
    def path(self) -> str:
        """Location of the database file (read-only)."""
        return self._db_path

    # ------------------------------------------------------------------
    # Public methods (what DataManager is allowed to call)
    # ------------------------------------------------------------------

    def load(self) -> list[Record]:
        """READ: load all valid records from the database.

        - New or empty database: records are imported from the backup file
          (this is also how Part 1 JSON data moves into SQLite on first run).
        - Corrupt database: the file is kept as *.corrupt.db, a new database is
          created, and records are recovered from the backup.
        - Database cannot be opened (locked, no permission): records are taken
          from the backup in memory, and the database file is left alone.
        """
        is_new = not os.path.exists(self._db_path)

        try:
            rows = self._select_all_rows()
        except sqlite3.OperationalError:
            # Must come before DatabaseError: OperationalError is a child of it.
            return self._records_from_backup_in_memory(
                "Could not open the database."
            )
        except sqlite3.DatabaseError:
            preserved = self._preserve_corrupt_database()
            if preserved:
                reason = "Database file was corrupt. Retrieving from Backup."
            else:
                reason = "Database file was corrupt; could not preserve its contents."
            return self._rebuild_from_backup(reason, report_if_no_backup=True)

        if not rows:
            reason = "New database created." if is_new else "Database was empty."
            return self._rebuild_from_backup(reason, report_if_no_backup=False)

        entries, bad_rows = self._rows_to_entries(rows)
        records, skipped = RecordConverter.from_list(entries)
        skipped += bad_rows
        self._status_message = (
            f"Skipped {skipped} invalid record(s)." if skipped > 0 else ""
        )
        return records

    def save_all(self, records: list[Record]) -> tuple[bool, str]:
        """CREATE / UPDATE / DELETE: make the table match `records`.

        New record_ids are INSERTed, existing ones are UPDATEd, and ids no
        longer in the list are DELETEd, all in one transaction.
        Then the backup file is updated.

        Returns (True, "") on success, (True, "warning") if only the backup
        failed, or (False, "reason") if nothing was saved.
        """
        for record in records:
            is_valid, error = RecordConverter.check_record(record)
            if not is_valid:
                return False, error

        try:
            rows = [self._record_to_row(record) for record in records]
            with closing(self._connect()) as connection:
                with connection:    # commits on success, rolls back on error
                    self._create_table(connection)
                    existing_ids = self._existing_ids(connection)
                    new_ids = set()
                    for row in rows:
                        record_id = row[0]
                        if record_id in existing_ids:
                            self._update_row(connection, row)
                        else:
                            self._insert_row(connection, row)
                        new_ids.add(record_id)
                    self._delete_rows(connection, existing_ids - new_ids)
        except sqlite3.IntegrityError:
            return False, "The database rejected a duplicate or invalid record."
        except (sqlite3.Error, TypeError, ValueError):
            return False, "Could not write to the database."

        # The backup is only updated after the database was saved.
        if not self._backup.update(records):
            return (
                True,
                "Records saved, but the backup database could not be updated. "
                "The previous backup was preserved where possible.",
            )
        return True, ""

    # ------------------------------------------------------------------
    # Private helpers: SQL (only used inside this class)
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection. The data folder is created if it is missing."""
        directory = os.path.dirname(os.path.abspath(self._db_path))
        os.makedirs(directory, exist_ok=True)
        return sqlite3.connect(self._db_path)

    def _create_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(self._CREATE_TABLE_SQL)

    def _select_all_rows(self) -> list[tuple]:
        """READ every row, oldest record first. Creates the table if needed."""
        columns = ", ".join(self.COLUMNS)
        with closing(self._connect()) as connection:
            with connection:
                self._create_table(connection)
                cursor = connection.execute(
                    f"SELECT {columns} FROM records ORDER BY record_id"
                )
                return cursor.fetchall()

    def _existing_ids(self, connection: sqlite3.Connection) -> set[int]:
        cursor = connection.execute("SELECT record_id FROM records")
        return {row[0] for row in cursor.fetchall()}

    def _insert_row(self, connection: sqlite3.Connection, row: tuple) -> None:
        """CREATE one row."""
        columns = ", ".join(self.COLUMNS)
        placeholders = ", ".join("?" for _ in self.COLUMNS)
        connection.execute(
            f"INSERT INTO records ({columns}) VALUES ({placeholders})", row
        )

    def _update_row(self, connection: sqlite3.Connection, row: tuple) -> None:
        """UPDATE one row, found by its record_id."""
        assignments = ", ".join(f"{column} = ?" for column in self.COLUMNS[1:])
        connection.execute(
            f"UPDATE records SET {assignments} WHERE record_id = ?",
            (*row[1:], row[0]),
        )

    def _delete_rows(self, connection: sqlite3.Connection, record_ids: set[int]) -> None:
        """DELETE every row whose record_id is in `record_ids`."""
        connection.executemany(
            "DELETE FROM records WHERE record_id = ?",
            [(record_id,) for record_id in record_ids],
        )

    # ------------------------------------------------------------------
    # Private helpers: converting between rows and records
    # ------------------------------------------------------------------

    def _record_to_row(self, record: Record) -> tuple:
        """Record -> tuple in COLUMNS order. The indicators list becomes JSON text."""
        data = RecordConverter.to_dict(record)
        data["indicators"] = json.dumps(data["indicators"])
        return tuple(data[column] for column in self.COLUMNS)

    def _rows_to_entries(self, rows: list[tuple]) -> tuple[list[dict], int]:
        """Rows -> dictionaries with the JSON key names, ready for RecordConverter.

        Returns (entries, bad_rows). A row whose indicators text is not a
        valid JSON list is counted as bad and skipped.
        """
        entries = []
        bad_rows = 0
        for row in rows:
            entry = dict(zip(self.COLUMNS, row))
            try:
                entry["indicators"] = json.loads(entry["indicators"])
            except (TypeError, json.JSONDecodeError):
                bad_rows += 1
                continue
            entries.append(entry)
        return entries, bad_rows

    # ------------------------------------------------------------------
    # Private helpers: recovery
    # ------------------------------------------------------------------

    def _rebuild_from_backup(self, reason: str, report_if_no_backup: bool) -> list[Record]:
        """Fill the database from the backup file and set the status message."""
        backup_records = self._backup.load_valid_records()

        if not backup_records:
            # An empty new database with no backup is normal, not a problem.
            self._status_message = (
                f"{reason} No valid backup records were available."
                if report_if_no_backup
                else ""
            )
            return []

        saved, _message = self.save_all(backup_records)
        if not saved:
            self._status_message = (
                f"{reason} Recovered records in memory, but could not "
                "restore the database."
            )
            return backup_records

        self._status_message = (
            f"{reason} Restored {len(backup_records)} record(s) from backup."
        )
        return backup_records

    def _records_from_backup_in_memory(self, reason: str) -> list[Record]:
        """Use the backup records without touching the database file."""
        backup_records = self._backup.load_valid_records()
        self._status_message = (
            f"{reason} Loaded {len(backup_records)} record(s) from backup; "
            "new records may not be saved."
        )
        return backup_records

    def _preserve_corrupt_database(self) -> str:
        """Rename a corrupt database to *.corrupt.db so its contents are not lost.

        e.g. scam_data.db -> scam_data.corrupt.db
        Returns the new name, or "" if the rename failed.
        """
        base, extension = os.path.splitext(self._db_path)
        preserved_name = f"{base}.corrupt{extension or '.db'}"
        try:
            os.replace(self._db_path, preserved_name)
        except OSError:
            return ""
        return preserved_name
