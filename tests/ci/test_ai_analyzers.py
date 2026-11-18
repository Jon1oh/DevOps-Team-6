"""Tests for the AI side of the app (Part 2).

Covers:
- GeminiAiAnalyzer with a FAKE Gemini client: valid JSON, JSON wrapped in
  extra text, API failure and retry
- FallbackAiAnalyzer (the local trained model): risk levels, indicators,
  recommendations and a full analysis
- AiManager: owns one Gemini analyzer and one fallback analyzer
- The analysis service (app/app.py) that the website uses: input validation,
  malformed AI output, fallback, business rules and saving the record

No test calls the real Gemini API: no internet and no API key are needed.

Run from the project root:  python -m pytest tests/test_ai_analyzers.py -v
"""

import json
from datetime import datetime
from types import SimpleNamespace

import pytest

import app.analyzers.gemini_analyzer as gemini_module
import managers.ai_manager as ai_manager_module
from app.analyzers.fallback_ai_analyzer import FallbackAiAnalyzer
from app.analyzers.gemini_analyzer import GeminiAiAnalyzer
from app.app import App as AnalysisService
from app.interfaces.ai_analyzer import AiAnalyzer
from app.models.record import Record
from app.storage.json_record_storage import JsonRecordStorage
from app.storage.record_converter import RecordConverter
from managers.ai_manager import AiManager
from managers.data_manager import DataManager
from managers.io_manager import IoManager
from managers.logic_manager import LogicManager


# ======================================================================
# A fake Gemini client (stands in for google.genai.Client)
# ======================================================================

class FakeModels:
    """Gives back prepared answers instead of calling Google.

    Each item in `outcomes` is used for one API call, in order:
    a string is returned as the response text, an Exception is raised.
    """

    def __init__(self):
        self.outcomes = []
        self.prompts = []

    def generate_content(self, model, contents):
        self.prompts.append(contents)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)


class FakeGeminiClient:
    def __init__(self, api_key=None):
        self.models = FakeModels()


class FakeErrorLogger:
    """Stands in for app.logger.ErrorLogger: keeps the messages in a list
    instead of writing to data/error.log, so tests never touch real files."""

    def __init__(self):
        self.messages = []

    def log_error(self, error):
        self.messages.append(str(error))


VALID_AI_JSON = {
    "scam_probability": 92,
    "risk_level": "HIGH",
    "scam_type": "Unexpected Prize Money Scam",
    "indicators": ["Suspicious links", "Unexpected prizes or winnings"],
    "explanation": "The message claims a prize the user never entered for.",
    "recommendation": "Do not click the link or reply.",
}

SCAM_MESSAGE = "Congratulations! You won $5,000. Claim now at http://cashprice-govsg.com"


@pytest.fixture
def error_logger():
    return FakeErrorLogger()


@pytest.fixture
def gemini(monkeypatch, error_logger):
    """A GeminiAiAnalyzer that uses the fake client instead of Google."""
    monkeypatch.setattr(gemini_module.genai, "Client", FakeGeminiClient)
    return GeminiAiAnalyzer(error_logger, model="test-model")


def set_responses(analyzer, *outcomes):
    """Tell the fake API what to answer on each call."""
    fake_models = analyzer._client.models
    fake_models.outcomes = list(outcomes)
    return fake_models


def new_record() -> Record:
    """A Record after the website has split the phone number."""
    return Record(phone_number="91234567", country_code="+65", message=SCAM_MESSAGE)


# ======================================================================
# GeminiAiAnalyzer
# ======================================================================

def test_valid_json_response_fills_the_record(gemini):
    set_responses(gemini, json.dumps(VALID_AI_JSON))

    record = gemini.analyze_message(new_record())

    assert record.scam_probability == 92
    assert record.risk_level == "HIGH"
    assert record.scam_type == "Unexpected Prize Money Scam"
    assert record.indicators == ["Suspicious links", "Unexpected prizes or winnings"]
    assert record.recommendation == "Do not click the link or reply."
    datetime.strptime(record.timestamp, "%Y-%m-%d %H:%M:%S")   # correct timestamp format


@pytest.mark.parametrize(
    "wrapped_response",
    [
        "Here is the analysis:\n" + json.dumps(VALID_AI_JSON) + "\nHope this helps!",
        "```json\n" + json.dumps(VALID_AI_JSON) + "\n```",
    ],
)
def test_json_wrapped_in_extra_text_is_still_read(gemini, wrapped_response, error_logger):
    set_responses(gemini, wrapped_response)

    record = gemini.analyze_message(new_record())

    assert record.risk_level == "HIGH"
    assert error_logger.messages[0].startswith("JSONDecode Error")   # first parse attempt logged


def test_prompt_contains_message_and_full_phone_number_and_asks_for_json(gemini):
    fake_models = set_responses(gemini, json.dumps(VALID_AI_JSON))

    gemini.analyze_message(new_record())

    prompt = fake_models.prompts[0]
    assert SCAM_MESSAGE in prompt
    assert "+6591234567" in prompt
    assert "Return only a JSON object" in prompt


def test_api_failure_then_successful_retry(gemini, error_logger):
    fake_models = set_responses(gemini, TimeoutError("timed out"), json.dumps(VALID_AI_JSON))

    record = gemini.analyze_message(new_record())

    assert record.risk_level == "HIGH"
    assert len(fake_models.prompts) == 2       # first call + one retry
    assert error_logger.messages == ["API Error: timed out"]


def test_api_failure_twice_returns_false(gemini, error_logger):
    fake_models = set_responses(gemini, ConnectionError("no network"), ConnectionError("still down"))

    assert gemini.analyze_message(new_record()) is False
    assert len(fake_models.prompts) == 2       # retried exactly once
    assert error_logger.messages == ["API Error: no network", "API Error: still down"]


# ======================================================================
# FallbackAiAnalyzer (local trained model, no internet)
# ======================================================================

@pytest.fixture(scope="module")
def fallback():
    return FallbackAiAnalyzer()


@pytest.mark.parametrize(
    "probability, expected_level",
    [(100, "HIGH"), (80, "HIGH"), (79, "MEDIUM"), (50, "MEDIUM"), (49, "LOW"), (0, "LOW")],
)
def test_fallback_risk_level_boundaries(fallback, probability, expected_level):
    assert fallback.get_risk_level(probability) == expected_level


@pytest.mark.parametrize(
    "message, expected_indicator",
    [
        ("You are the lucky draw winner!", "Unexpected prize claim"),
        ("Visit https://example-bank-verify.com", "Suspicious link"),
        ("Collect your $10,000 today", "Large financial reward"),
        ("Act now, this is your last chance", "Urgent or threatening language"),
        ("Your account suspended, verify your account", "Requests account verification"),
        ("Please send your OTP to us", "Requests sensitive personal information"),
        ("Please make a bank transfer today", "Requests payment or money transfer"),
        ("Cl@im your pr1ze", "Spelling mistakes"),
    ],
)
def test_fallback_detects_indicators(fallback, message, expected_indicator):
    assert expected_indicator in fallback.detect_indicators(message)


def test_fallback_finds_no_indicators_in_a_normal_message(fallback):
    assert fallback.detect_indicators("Hi mum, see you at dinner tonight") == []


def test_fallback_gives_a_recommendation_for_every_risk_level(fallback):
    for level in ("HIGH", "MEDIUM", "LOW"):
        assert fallback.generate_recommendation(level)


def test_fallback_full_analysis_of_a_scam_message(fallback):
    record = fallback.analyze_message(new_record())

    assert 0 <= record.scam_probability <= 100
    assert record.risk_level == fallback.get_risk_level(record.scam_probability)
    assert "Suspicious link" in record.indicators
    assert record.explanation and record.recommendation


def test_fallback_rejects_a_message_that_is_not_text(fallback):
    with pytest.raises(TypeError):
        fallback.analyze_message(Record(message=12345))


def test_both_analyzers_share_the_same_interface(gemini, fallback):
    """Polymorphism: the app can call analyze_message() on either one."""
    assert isinstance(gemini, AiAnalyzer)
    assert isinstance(fallback, AiAnalyzer)


# ======================================================================
# AiManager
# ======================================================================

def test_ai_manager_creates_and_keeps_one_of_each_analyzer(monkeypatch):
    monkeypatch.setattr(ai_manager_module, "GeminiAiAnalyzer", lambda error_logger: "gemini analyzer")
    monkeypatch.setattr(ai_manager_module, "FallbackAiAnalyzer", lambda: "fallback analyzer")

    manager = AiManager(FakeErrorLogger())

    assert manager.get_analyzer() == "gemini analyzer"
    assert manager.get_fallback_analyzer() == "fallback analyzer"


# ======================================================================
# Analysis service (app/app.py): the full pipeline the website runs
# ======================================================================

class FakeAiManager:
    """Hands the service our test analyzers instead of creating real ones."""

    def __init__(self, analyzer, fallback_analyzer):
        self._analyzer = analyzer
        self._fallback = fallback_analyzer

    def get_analyzer(self):
        return self._analyzer

    def get_fallback_analyzer(self):
        return self._fallback


class BrokenAnalyzer:
    def analyze_message(self, record):
        raise RuntimeError("model file damaged")


@pytest.fixture
def service_parts(gemini, fallback, error_logger, tmp_path):
    """Real managers on temporary data files, Gemini replaced by the fake client."""
    data_manager = DataManager(JsonRecordStorage(str(tmp_path / "scam_data.json"),
                                                 str(tmp_path / "backup_database.json")))
    service = AnalysisService(FakeAiManager(gemini, fallback), data_manager, LogicManager(),
                              RecordConverter(), IoManager(), error_logger)
    return service, data_manager


def website_record(phone="+6591234567", message=SCAM_MESSAGE) -> Record:
    """A Record exactly as routes.py creates it from the scanner form."""
    return Record(timestamp="2026-11-16 18:00:00", phone_number=phone, message=message)


def test_service_analyses_and_saves_a_message(service_parts, gemini):
    service, data_manager = service_parts
    set_responses(gemini, json.dumps(VALID_AI_JSON))

    result = service.analyze_record(website_record())

    assert result["status"] == "complete"
    assert result["saved"] is True
    saved = data_manager.find_record(1)
    assert (saved.phone_number, saved.country_code) == ("91234567", "+65")   # number split
    assert saved.risk_level == "HIGH"
    assert saved.country_name == "Singapore"


@pytest.mark.parametrize(
    "phone, message, expected_error",
    [
        ("abc", SCAM_MESSAGE, "Enter a valid international phone number."),
        ("91234567", SCAM_MESSAGE, "Enter a valid international phone number."),   # no country code
        ("+6591234567", "hi !!", "Enter a more meaningful message"),
    ],
)
def test_service_rejects_invalid_input_before_calling_the_ai(service_parts, gemini, phone, message, expected_error):
    service, data_manager = service_parts
    fake_models = set_responses(gemini)        # no answers prepared: the AI must not be called

    result = service.analyze_record(website_record(phone, message))

    assert result == {"status": "error", "message": expected_error}
    assert fake_models.prompts == []
    assert data_manager.records == []


@pytest.mark.parametrize(
    "bad_response",
    [
        "Sorry, I cannot help with that.",                     # no JSON at all
        '{"scam_probability": 92, "risk_level": ',             # cut-off JSON
        json.dumps({"scam_probability": 92}),                   # missing fields
        None,                                                   # empty response
    ],
)
def test_malformed_ai_output_offers_the_fallback_instead_of_crashing(service_parts, gemini, bad_response, error_logger):
    service, data_manager = service_parts
    set_responses(gemini, bad_response)

    result = service.analyze_record(website_record())

    assert result["status"] == "fallback_required"
    assert "Primary AI analysis failed." in error_logger.messages   # written to the error log
    assert data_manager.records == []                       # nothing half-saved


def test_api_down_twice_offers_the_fallback(service_parts, gemini):
    service, _data_manager = service_parts
    set_responses(gemini, ConnectionError("down"), ConnectionError("still down"))

    assert service.analyze_record(website_record())["status"] == "fallback_required"


def test_fallback_analysis_completes_and_is_saved(service_parts):
    service, data_manager = service_parts
    record = website_record()
    record.phone_number, record.country_code = "91234567", "+65"   # already split by analyze_record

    result = service.analyze_with_fallback_ai(record)

    assert result["status"] == "complete"
    assert result["saved"] is True
    assert len(data_manager.records) == 1


def test_fallback_failure_returns_an_error_not_a_crash(gemini, error_logger, tmp_path):
    data_manager = DataManager(JsonRecordStorage(str(tmp_path / "d.json"), str(tmp_path / "b.json")))
    service = AnalysisService(FakeAiManager(gemini, BrokenAnalyzer()), data_manager, LogicManager(),
                              RecordConverter(), IoManager(), error_logger)

    result = service.analyze_with_fallback_ai(new_record())

    assert result == {"status": "error", "message": "model file damaged"}
    assert "Fallback AI analysis failed." in error_logger.messages


def test_ai_output_with_wrong_field_types_is_rejected(service_parts, gemini):
    service, data_manager = service_parts
    set_responses(gemini, json.dumps(dict(VALID_AI_JSON, scam_probability="very high")))

    result = service.analyze_record(website_record())

    assert result == {"status": "error", "message": "One of the fields in the AI output is invalid."}
    assert data_manager.records == []


def test_business_rules_correct_an_over_scored_message(service_parts, gemini):
    service, data_manager = service_parts
    # The AI says HIGH but found no indicators
    set_responses(gemini, json.dumps(dict(VALID_AI_JSON, scam_probability=85, indicators=[])))

    service.analyze_record(website_record())

    saved = data_manager.find_record(1)
    assert saved.risk_level == "LOW"
    assert saved.scam_probability == 49
    assert saved.indicators == ["NIL"]


def test_number_flagged_before_is_escalated_to_high(service_parts, gemini):
    service, data_manager = service_parts
    set_responses(gemini, json.dumps(VALID_AI_JSON),
                  json.dumps(dict(VALID_AI_JSON, scam_probability=20, risk_level="LOW", indicators=[])))

    service.analyze_record(website_record())                     # 1st: HIGH risk
    result = service.analyze_record(website_record())            # 2nd: AI says LOW

    assert result["record"].risk_level == "HIGH"
    assert "91234567 was found in 1 High Risk Incidents." in result["record"].indicators


def test_dashboard_and_history_data(service_parts, gemini):
    service, _data_manager = service_parts
    set_responses(gemini, json.dumps(VALID_AI_JSON),
                  json.dumps(dict(VALID_AI_JSON, scam_probability=10, risk_level="LOW", indicators=[])))
    service.analyze_record(website_record())
    service.analyze_record(website_record(phone="+447911123456"))

    dashboard = service.get_dashboard_data()
    history = service.get_history_records()

    assert dashboard["statistics"] == {"total": 2, "high": 1, "medium": 0, "low": 1}
    assert [record.record_id for record in history] == [2, 1]      # newest first
