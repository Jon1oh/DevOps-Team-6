from pathlib import Path
import os, secrets, logging
from dotenv import load_dotenv
from flask import Flask
from managers.ai_manager import AiManager
from managers.data_manager import DataManager
from managers.logic_manager import LogicManager
from managers.io_manager import IoManager
from storage.json_record_storage import JsonRecordStorage
from storage.record_converter import RecordConverter
from .app import App

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv()
logging.getLogger().setLevel(logging.ERROR) # hide warning messages from the Gemini SDK which uses Python's logging module

flask_app = Flask(__name__)
flask_app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

ai_manager = AiManager()
data_manager = DataManager(JsonRecordStorage())
logic_manager = LogicManager()
record_converter = RecordConverter()
io_manager = IoManager()

analysis_service = App(ai_manager, data_manager, logic_manager, record_converter,io_manager)

# Import last so the route decorators register on this Flask app.
from . import routes

