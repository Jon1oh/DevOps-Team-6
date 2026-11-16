# AI Scam Message Detector (INF1103 Team 6)

A Flask web app that analyses suspicious SMS messages with Google Gemini, with an in-house fallback AI model when Gemini is unavailable. Messages can be typed in, or read from a screenshot with OCR (Tesseract).

# API key

1. Copy `.env.example` to `.env`.
2. Replace `PUTYOURAPIKEYHERE` with your own Gemini API key.

`.env` is listed in `.gitignore` and `.dockerignore`, so the key is never committed to GitHub or copied into the Docker image.

# How to run the program with Docker

```powershell
docker load -i ai_scam_detector_image.tar
```
1. Import the docker image (or build it from the source code, see below).

```powershell
docker images
```
2. Verify the image exists and is loaded.

```powershell
docker volume create scam-db
```
3. Create a persistent docker volume for the program to store its database files.

```powershell
docker run --rm -it -p 8000:8000 --env-file .env -v scam-db:/app/data ai_scam_detector
```
4. Run the application, then open **http://localhost:8000** in a browser. `-p 8000:8000` makes the website reachable from your browser, and `--env-file .env` passes in your Gemini API key at run time.

# Building the image from the source code

```bash
docker build -f dockerfile -t ai_scam_detector .
```

# Running without Docker

Requires Python 3.11+ and Tesseract OCR (`brew install tesseract` on macOS, `sudo apt-get install tesseract-ocr` on Ubuntu).

```bash
python -m pip install -r requirements.txt
python run.py
```
Then open **http://localhost:8000**.

# Running the automated tests

The tests do not call the live Gemini API (they use a fake client with prepared responses), so no API key or internet connection is needed.

**Inside Docker** (no Python installation needed):

```bash
docker run --rm ai_scam_detector python -m pytest tests -v
```

**Without Docker:**

```bash
python -m pytest tests -v
```

| Test file | What it covers |
|---|---|
| `tests/logic_test.py` | LogicManager business rules: AI output validation, risk levels, indicator checks, escalation of previously flagged numbers |
| `tests/test_ai_analyzers.py` | Gemini analyzer with a mocked API (valid and wrapped responses, API failure and retry), fallback AI model, AiManager, and the analysis service: input validation, malformed AI output, fallback, business rules and saving |
| `tests/test_data_manager.py` | DataManager, JSON storage recovery (missing, empty, corrupt and wrongly formatted files), RecordConverter validation and summary statistics |
| `tests/test_io_manager.py` | Phone number validation and splitting, message checks |
| `tests/test_web_routes.py` | Flask web interface (advanced feature): every page, scanner, fallback prompt, screenshot upload limits, crop and OCR flow |
| `tests/test_ocr_reader.py` | OCR (new feature): crop box, empty and invalid images, Tesseract missing, and a real OCR read when Tesseract is installed |

# Continuous Integration

`.github/workflows/tests.yml` runs on every push and pull request. It runs the test suite with Python 3.11, then builds the Docker image and runs the same tests inside the container. Results are shown in the **Actions** tab on GitHub and as a check on each pull request.
