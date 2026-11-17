from pathlib import Path
import os, secrets, logging, tempfile
from dotenv import load_dotenv
from flask import Flask
from managers.ai_manager import AiManager
from managers.data_manager import DataManager
from managers.logic_manager import LogicManager
from managers.io_manager import IoManager
from app.storage.json_record_storage import JsonRecordStorage
from app.storage.record_converter import RecordConverter
from .ocr_reader import OcrReader
from .logger import ErrorLogger
from .app import App

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv()
logging.getLogger().setLevel(logging.ERROR) # hide warning messages from the Gemini SDK which uses Python's logging module

# Uploads go in the system temp folder, created automatically if missing
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "scamguard_ocr")
ALLOWED_TYPES = {".png", ".jpg", ".jpeg"}
MIN_UPLOAD_BYTES = 1024 # 1 KB
MAX_UPLOAD_BYTES = 5242880 # 5 MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

flask_app = Flask(__name__)
flask_app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
flask_app.config["MAX_CONTENT_LENGTH"] = 6291456 # Flask rejects anything over 6 MB before reading it (error 413, handled below)

error_logger = ErrorLogger()
ai_manager = AiManager(error_logger)
data_manager = DataManager(JsonRecordStorage())
logic_manager = LogicManager()
record_converter = RecordConverter()
io_manager = IoManager()
ocr = OcrReader()

analysis_service = App(ai_manager, data_manager, logic_manager, record_converter, io_manager, error_logger)

# Import last so the route decorators register on this Flask app.
from . import routes