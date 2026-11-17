import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "data" / "error.log"

def configure_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    file_handler = next(
        (handler for handler in root_logger.handlers
         if getattr(handler, "_scamguard_file", False)),
        None,
    )
    if file_handler is None:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler._scamguard_file = True
        root_logger.addHandler(file_handler)

    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    console_handler = next(
        (handler for handler in root_logger.handlers
         if getattr(handler, "_scamguard_console", False)),
        None,
    )
    if console_handler is None:
        console_handler = logging.StreamHandler()
        console_handler._scamguard_console = True
        root_logger.addHandler(console_handler)

    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)