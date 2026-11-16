import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "data" / "error.log"

def configure_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)

    if not any(getattr(h, "_scamguard_file", False) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler._scamguard_file = True
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        root_logger.addHandler(file_handler)

    if not any(getattr(h, "_scamguard_console", False) for h in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler._scamguard_console = True
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        ))
        root_logger.addHandler(console_handler)