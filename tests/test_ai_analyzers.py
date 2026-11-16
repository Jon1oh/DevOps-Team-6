"""Tests for the AI side of the app (Part 2).

Covers:
- GeminiAiAnalyzer with a FAKE Gemini client: valid JSON, JSON wrapped in
  extra text, malformed output, missing fields, API failure and retry
- FallbackAiAnalyzer (the local trained model): risk levels, indicators,
  recommendations and a full analysis
- AiManager: owns one Gemini analyzer and one fallback analyzer
- The full pipeline the app runs: AI analysis -> LogicManager checks ->
  DataManager saves the record

No test calls the real Gemini API: no internet and no API key are needed.

Run from the project root:  python -m pytest tests/test_ai_analyzers.py -v
"""

import json
from datetime import datetime
from types import SimpleNamespace

import pytest

import analyzers.gemini_analyzer as gemini_module
import managers.ai_manager as ai_manager_module
from analyzers.fallback_ai_analyzer import FallbackAiAnalyzer
from analyzers.gemini_analyzer import GeminiAiAnalyzer
from interfaces.ai_analyzer import AiAnalyzer
from managers.ai_manager import AiManager
from managers.data_manager import DataManager
from managers.logic_manager import LogicManager
from models.record import Record
from storage.json_record_storage import JsonRecordStorage
from storage.record_converter import RecordConverter


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
def gemini(monkeypatch):
    """A GeminiAiAnalyzer that uses the fake client and records logged errors."""
    monkeypatch.setattr(gemini_module.genai, "Client", FakeGeminiClient)
    analyzer = GeminiAiAnalyzer(model="test-model")
    analyzer.logged_errors = []
    # Keep test errors out of the real data/error.log file
    monkeypatch.setattr(analyzer, "log_error", lambda error: analyzer.logged_errors.append(str(error)))
    return analyzer


def set_responses(analyzer, *outcomes):
    """Tell the fake API what to answer on each call."""
    fake_models = analyzer._client.models
    fake_models.outcomes = list(outcomes)
    return fake_models


def new_record() -> Record:
    """A Record the way app.py creates it before AI analysis."""
    return Record(phone_number="91234567", country_code="+65", message=SCAM_MESSAGE)


# ======================================================================
# GeminiAiAnalyzer: valid responses
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
    assert gemini.logged_errors == []


@pytest.mark.parametrize(
    "wrapped_response",
    [
        "Here is the analysis:\n" + json.dumps(VALID_AI_JSON) + "\nHope this helps!",
        "```json\n" + json.dumps(VALID_AI_JSON) + "\n```",
    ],
)
def test_json_wrapped_in_extra_text_is_still_read(gemini, wrapped_response):
    set_responses(gemini, wrapped_response)

    record = gemini.analyze_message(new_record())

    assert record.risk_level == "HIGH"
    assert len(gemini.logged_errors) == 1     # the first parse attempt is logged


def test_prompt_contains_message_and_full_phone_number_and_asks_for_json(gemini):
    fake_models = set_responses(gemini, json.dumps(VALID_AI_JSON))

    gemini.analyze_message(new_record())

    prompt = fake_models.prompts[0]
    assert SCAM_MESSAGE in prompt
    assert "+6591234567" in prompt
    assert "Return only a JSON object" in prompt
    for field in GeminiAiAnalyzer.REQUIRED_FIELDS:
        assert field in prompt


# ======================================================================
# GeminiAiAnalyzer: malformed responses (must not crash)
# ======================================================================

@pytest.mark.parametrize(
    "bad_response, expected_log",
    [
        ("Sorry, I cannot help with that.", "did not contain a JSON object"),
        ('{"scam_probability": 92, "risk_level": ', "Expecting"),            # cut-off JSON
        (json.dumps([VALID_AI_JSON]), "did not contain a JSON object"),     # a list, not an object
        (None, "empty or not text"),                                          # API gave no text
    ],
)
def test_malformed_response_returns_false_and_is_logged(gemini, bad_response, expected_log):
    set_responses(gemini, bad_response)

    result = gemini.analyze_message(new_record())

    assert result is False                    # app.py then offers the fallback AI
    assert any(expected_log in error for error in gemini.logged_errors)


def test_response_missing_fields_returns_false_and_names_them(gemini):
    incomplete = dict(VALID_AI_JSON)
    del incomplete["risk_level"]
    del incomplete["recommendation"]
    set_responses(gemini, json.dumps(incomplete))

    result = gemini.analyze_message(new_record())

    assert result is False
    assert gemini.logged_errors == ["AI response is missing fields: risk_level, recommendation"]


def test_response_with_wrong_field_types_is_caught_by_logic_manager(gemini):
    """The fields exist, so the analyzer fills the Record; LogicManager then rejects it."""
    wrong_types = dict(VALID_AI_JSON, scam_probability="very high")
    set_responses(gemini, json.dumps(wrong_types))

    record = gemini.analyze_message(new_record())

    assert LogicManager().check_ai_output(record) is False


# ======================================================================
# GeminiAiAnalyzer: API failure and retry
# ======================================================================

def test_api_failure_then_successful_retry(gemini):
    fake_models = set_responses(gemini, TimeoutError("timed out"), json.dumps(VALID_AI_JSON))

    record = gemini.analyze_message(new_record())

    assert record.risk_level == "HIGH"
    assert len(fake_models.prompts) == 2       # first call + one retry
    assert gemini.logged_errors == ["timed out"]


def test_api_failure_twice_returns_false(gemini):
    fake_models = set_responses(gemini, ConnectionError("no network"), ConnectionError("still down"))

    result = gemini.analyze_message(new_record())

    assert result is False
    assert len(fake_models.prompts) == 2       # retried exactly once
    assert gemini.logged_errors == ["no network", "still down"]


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
    assert LogicManager().check_ai_output(record) is True


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
    monkeypatch.setattr(ai_manager_module, "GeminiAiAnalyzer", lambda: "gemini analyzer")
    monkeypatch.setattr(ai_manager_module, "FallbackAiAnalyzer", lambda: "fallback analyzer")

    manager = AiManager()

    assert manager.get_analyzer() == "gemini analyzer"
    assert manager.get_fallback_analyzer() == "fallback analyzer"
    assert manager.get_analyzer() is manager.get_analyzer()     # same object every time


# ======================================================================
# Full pipeline: the same steps as app.py, with the fake AI
# ======================================================================

def test_full_pipeline_ai_to_logic_to_saved_record(gemini, tmp_path):
    logic = LogicManager()
    data = DataManager(JsonRecordStorage(str(tmp_path / "scam_data.json"),
                                         str(tmp_path / "backup_database.json")))
    # The AI over-scores a message that has no indicators
    set_responses(gemini, json.dumps(dict(VALID_AI_JSON, scam_probability=85, indicators=[])))

    record = gemini.analyze_message(new_record())
    assert logic.check_ai_output(record) is True
    record = logic.format_ai_output(record)
    record = logic.validate_risk_assessment(record)        # business rules adjust the result
    record = logic.escalate_flagged_number(record, data.count_risk_levels(record.phone_number))
    saved, message = data.save_record(RecordConverter.to_dict(record))

    assert (saved, message) == (True, "")
    stored = data.find_record(1)
    assert stored.risk_level == "LOW"                      # no indicators -> not HIGH
    assert stored.scam_probability == 49                   # capped to the LOW range
    assert stored.indicators == ["NIL"]
    assert stored.scam_type == "Unexpected Prize Money Scam"


def test_full_pipeline_escalates_a_number_flagged_before(gemini, tmp_path):
    logic = LogicManager()
    data = DataManager(JsonRecordStorage(str(tmp_path / "scam_data.json"),
                                         str(tmp_path / "backup_database.json")))
    # An earlier HIGH-risk record from the same number
    data.save_record({
        "timestamp": "2026-11-01 09:00:00", "phone_number": "91234567", "country_code": "+65",
        "message_content": "Earlier scam", "scam_probability": 95, "risk_level": "HIGH",
        "scam_type": "Banking Scam", "indicators": ["Suspicious links"],
        "explanation": "x", "recommendation": "y",
    })
    set_responses(gemini, json.dumps(dict(VALID_AI_JSON, scam_probability=20,
                                          risk_level="LOW", indicators=[])))

    record = gemini.analyze_message(new_record())
    record = logic.validate_risk_assessment(logic.format_ai_output(record))
    record = logic.escalate_flagged_number(record, data.count_risk_levels(record.phone_number))

    assert record.risk_level == "HIGH"                     # escalated by the multi-condition rule
    assert "91234567 was found in 1 High Risk Incidents." in record.indicators
