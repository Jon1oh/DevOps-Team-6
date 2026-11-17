from datetime import datetime, timezone, timedelta
from pathlib import Path

class ErrorLogger:
    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent
        self._log_path = project_root / "data" / "error.log"
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_error(self, error):
        utc_plus_8 = timezone(timedelta(hours=8))
        timestamp = datetime.now(utc_plus_8)
        with self._log_path.open("a", encoding="utf-8") as logfile:
            logfile.write(f"{timestamp} - {error}\n")