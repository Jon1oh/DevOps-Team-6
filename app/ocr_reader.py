# Reads text from part of an image using Tesseract OCR.
# Only change this file to use a different OCR tool, routes.py remains unchanged

import os

import pytesseract
from PIL import Image

# Find the install location of tesseract by checking usual install location
# File does not exist in docker
WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(WINDOWS_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT


class OcrReader:

    def read_area(self, image_path: str, x: int, y: int, width: int, height: int) -> str:
        """Crop the box (x, y, width, height) out of the image and return its text.

        Always returns a string: "" if the image or Tesseract could not be used.
        """
        try:
            with Image.open(image_path) as image:
                area = image.crop((x, y, x + width, y + height))
                return pytesseract.image_to_string(area).strip()
        except (OSError, pytesseract.TesseractError, pytesseract.TesseractNotFoundError):
            return ""