"""Tests for the new feature: reading text from a screenshot (OcrReader).

Most tests replace Tesseract with a stand-in, so they run anywhere.
The last test uses the real Tesseract program and is skipped automatically
when it is not installed (it IS installed in the Docker image).

Run from the project root:  python -m pytest tests/test_ocr_reader.py -v
"""

import shutil

import pytest
from PIL import Image, ImageDraw, ImageFont

import app.ocr_reader as ocr_module
from app.ocr_reader import OcrReader


@pytest.fixture
def screenshot(tmp_path):
    """A white 400 x 200 image saved as a PNG file."""
    path = tmp_path / "screenshot.png"
    Image.new("RGB", (400, 200), "white").save(path)
    return str(path)


def test_only_the_cropped_box_is_read_and_text_is_trimmed(screenshot, monkeypatch):
    seen = {}

    def fake_tesseract(image):
        seen["size"] = image.size
        return "  You won a prize!\n"

    monkeypatch.setattr(ocr_module.pytesseract, "image_to_string", fake_tesseract)

    text = OcrReader().read_area(screenshot, 10, 20, 150, 60)

    assert text == "You won a prize!"
    assert seen["size"] == (150, 60)            # x, y, width, height -> crop box


def test_missing_image_returns_empty_text(tmp_path):
    assert OcrReader().read_area(str(tmp_path / "gone.png"), 0, 0, 10, 10) == ""


def test_file_that_is_not_an_image_returns_empty_text(tmp_path):
    fake_image = tmp_path / "fake.png"
    fake_image.write_text("this is not a picture")
    assert OcrReader().read_area(str(fake_image), 0, 0, 10, 10) == ""


def test_tesseract_not_installed_returns_empty_text(screenshot, monkeypatch):
    def not_installed(image):
        raise ocr_module.pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(ocr_module.pytesseract, "image_to_string", not_installed)

    assert OcrReader().read_area(screenshot, 0, 0, 100, 100) == ""


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_real_ocr_reads_a_phone_number_from_an_image(tmp_path):
    path = tmp_path / "sms.png"
    image = Image.new("RGB", (700, 140), "white")
    font = ImageFont.load_default(size=56)
    ImageDraw.Draw(image).text((20, 30), "+65 91234567", fill="black", font=font)
    image.save(path)

    text = OcrReader().read_area(str(path), 0, 0, 700, 140)

    assert "91234567" in text.replace(" ", "")
