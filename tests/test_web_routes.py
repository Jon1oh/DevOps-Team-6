"""Tests for the advanced feature: the Flask web interface (app/routes.py).

Flask's test client sends requests to the pages without starting a server.
The analysis service and the OCR reader are replaced with stand-ins, so no AI
is called, no real records are saved and Tesseract is not needed.

Run from the project root:  python -m pytest tests/test_web_routes.py -v
"""

import io
import os

import pytest
from PIL import Image

import app.routes as routes
import app.utils as utils
from app.models.record import Record
from app import flask_app


def analysed_record() -> Record:
    return Record(
        record_id=1, timestamp="2026-11-16 18:00:00", phone_number="91234567",
        country_code="+65", message="You won $5,000! Claim at http://cashprice-govsg.com",
        scam_probability=92, risk_level="HIGH", scam_type="Unexpected Prize Money Scam",
        indicators=["Suspicious links"], explanation="Fake prize.",
        recommendation="Do not click the link.",
    )


class FakeAnalysisService:
    """Stands in for app/app.py and remembers what the pages asked it to do."""

    def __init__(self):
        self.next_result = {"status": "complete", "record": analysed_record(),
                            "saved": True, "save_message": ""}
        self.analysed = []
        self.fallback_analysed = []

    def analyze_record(self, record):
        self.analysed.append(record)
        return self.next_result

    def analyze_with_fallback_ai(self, record):
        self.fallback_analysed.append(record)
        return {"status": "complete", "record": analysed_record(), "saved": True, "save_message": ""}

    def get_dashboard_data(self):
        return {"statistics": {"total": 7, "high": 3, "medium": 2, "low": 2},
                "recent_records": [analysed_record()]}

    def get_history_records(self):
        return [analysed_record()]


class FakeOcr:
    def __init__(self, texts):
        self.texts = list(texts)

    def read_area(self, image_path, x, y, width, height):
        return self.texts.pop(0)


@pytest.fixture
def service(monkeypatch):
    fake = FakeAnalysisService()
    monkeypatch.setattr(routes, "analysis_service", fake)
    monkeypatch.setattr(utils, "analysis_service", fake)
    return fake


@pytest.fixture
def upload_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(routes, "UPLOAD_FOLDER", str(tmp_path))
    return tmp_path


@pytest.fixture
def client(service, upload_folder):
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def png_bytes() -> bytes:
    """A real PNG image larger than the 1 KB minimum."""
    image = Image.frombytes("RGB", (64, 64), os.urandom(64 * 64 * 3))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def page(response) -> str:
    return response.get_data(as_text=True)


# ======================================================================
# Pages open
# ======================================================================

@pytest.mark.parametrize("url", ["/", "/history", "/scanner", "/screenshot"])
def test_every_page_opens(client, url):
    assert client.get(url).status_code == 200


def test_dashboard_shows_the_statistics(client):
    text = page(client.get("/"))
    assert "7" in text and "Unexpected Prize Money Scam" in text


# ======================================================================
# Scanner: analysing a typed message
# ======================================================================

def test_scanner_needs_both_phone_number_and_message(client, service):
    response = client.post("/scanner", data={"phone_number": "+6591234567", "message": ""})

    assert "Please enter both a phone number and message." in page(response)
    assert service.analysed == []                       # the AI was never called


def test_scanner_shows_the_analysis_result(client, service):
    response = client.post("/scanner", data={"phone_number": "+6591234567",
                                             "message": "You won $5,000! Claim now"})

    text = page(response)
    assert "HIGH" in text and "Unexpected Prize Money Scam" in text
    assert service.analysed[0].phone_number == "+6591234567"
    assert service.analysed[0].message == "You won $5,000! Claim now"


def test_scanner_shows_errors_from_the_service(client, service):
    service.next_result = {"status": "error", "message": "Enter a valid international phone number."}

    response = client.post("/scanner", data={"phone_number": "abc", "message": "Hello there friend"})

    assert "Enter a valid international phone number." in page(response)


# ======================================================================
# Scanner: Gemini unavailable -> ask before using the fallback AI
# ======================================================================

def ask_for_fallback(client, service):
    service.next_result = {"status": "fallback_required", "record": None}
    return client.post("/scanner", data={"phone_number": "+6591234567",
                                         "message": "Your parcel is waiting, pay now"})


def test_user_is_asked_before_the_fallback_ai_is_used(client, service):
    text = page(ask_for_fallback(client, service))

    assert "fallback" in text.lower()
    assert "Your parcel is waiting, pay now" in text
    assert service.fallback_analysed == []              # not used until the user agrees


def test_user_accepts_the_fallback_ai(client, service):
    ask_for_fallback(client, service)

    response = client.post("/scanner", data={"fallback_choice": "yes"})

    assert "HIGH" in page(response)
    assert service.fallback_analysed[0].message == "Your parcel is waiting, pay now"


def test_user_declines_the_fallback_ai(client, service):
    ask_for_fallback(client, service)

    response = client.post("/scanner", data={"fallback_choice": "no"})

    assert "Message analysis cancelled" in page(response)
    assert service.fallback_analysed == []


def test_fallback_answer_without_a_pending_scan_is_rejected(client, service):
    response = client.post("/scanner", data={"fallback_choice": "yes"})

    assert "expired" in page(response)
    assert service.fallback_analysed == []


# ======================================================================
# Screenshot upload (new feature, step 1)
# ======================================================================

def upload(client, content: bytes, filename: str):
    return client.post("/screenshot", data={"file": (io.BytesIO(content), filename)},
                       content_type="multipart/form-data")


def test_upload_without_a_file(client):
    assert "Please choose an image." in page(client.post("/screenshot", data={}))


def test_upload_rejects_files_that_are_not_png_or_jpg(client):
    assert "Please upload a PNG or JPG image." in page(upload(client, b"x" * 2000, "notes.txt"))


def test_upload_rejects_tiny_files(client):
    assert "too small" in page(upload(client, b"x" * 100, "tiny.png"))


def test_upload_rejects_files_over_5_mb(client):
    assert "too large" in page(upload(client, b"x" * (5 * 1024 * 1024 + 1), "big.png"))


def test_upload_over_6_mb_is_stopped_by_flask(client):
    response = upload(client, b"x" * (7 * 1024 * 1024), "huge.png")

    assert response.status_code == 413
    assert "too large" in page(response)


def test_valid_upload_is_saved_and_goes_to_the_crop_page(client, upload_folder):
    response = upload(client, png_bytes(), "sms.PNG")

    assert response.status_code == 302
    assert "/screenshot/crop/" in response.headers["Location"]
    saved_files = os.listdir(upload_folder)
    assert len(saved_files) == 1 and saved_files[0].endswith(".png")   # random name, not "sms"


# ======================================================================
# Crop and read text (new feature, step 2)
# ======================================================================

BOXES = {"x1": "0", "y1": "0", "width1": "60", "height1": "20",
         "x2": "0", "y2": "20", "width2": "60", "height2": "40"}


@pytest.fixture
def uploaded_image(upload_folder):
    path = upload_folder / "abc123.png"
    path.write_bytes(png_bytes())
    return path


def test_crop_page_for_an_unknown_file_is_not_found(client):
    assert client.get("/screenshot/crop/not-there.png").status_code == 404


def test_crop_page_opens_for_an_uploaded_image(client, uploaded_image):
    assert client.get("/screenshot/crop/abc123.png").status_code == 200


def test_crop_without_both_boxes_asks_again(client, uploaded_image):
    response = client.post("/screenshot/crop/abc123.png", data={"x1": "0"})

    assert "Please draw both crop boxes" in page(response)
    assert uploaded_image.exists()                       # kept so the user can retry


def test_text_read_from_both_boxes_fills_the_scanner(client, uploaded_image, monkeypatch):
    monkeypatch.setattr(routes, "ocr", FakeOcr(["+65 91234567", "Your parcel is held, pay $2 now"]))

    text = page(client.post("/screenshot/crop/abc123.png", data=BOXES))

    assert "+65 91234567" in text
    assert "Your parcel is held, pay $2 now" in text
    assert not uploaded_image.exists()                   # screenshot deleted after reading


def test_no_text_found_tells_the_user(client, uploaded_image, monkeypatch):
    monkeypatch.setattr(routes, "ocr", FakeOcr(["", ""]))

    text = page(client.post("/screenshot/crop/abc123.png", data=BOXES))

    assert "No text could be read" in text
    assert not uploaded_image.exists()
