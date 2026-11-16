# How to run the program with docker

```powershell
docker load -i ai_scam_detector_image.tar
```
1. Import the docker image.

```powershell
docker images
```
2. Verify the image exists and is loaded.

```powershell
docker volume create scam-db
```

3. Create a persistent docker volume for the program to store its database files.

```powershell
docker run --rm -it --env-file .env -v scam-db:/app/data ai_scam_detector
```
4. Run the application. `--env-file .env` passes in your Gemini API key (see "API key" below); the key is never stored inside the image. It will start with an empty database.

# API key

The app reads the Gemini API key from a `.env` file in the project root:

1. Copy `.env.example` to `.env`.
2. Replace `PUTYOURAPIKEYHERE` with your own Gemini API key.

`.env` is listed in `.gitignore` and `.dockerignore`, so the key is never committed to GitHub or copied into the Docker image. Without a key the app still runs: when the Gemini API is unavailable, it offers the in-house fallback AI model.

# Building the image from the source code

```bash
docker build -f dockerfile -t ai_scam_detector .
```

# Running the automated tests

The tests do not call the live Gemini API (they use a fake client with prepared responses), so no API key or internet connection is needed.

**Inside Docker** (no Python installation needed):

```bash
docker run --rm ai_scam_detector python -m pytest tests -v
```

**Without Docker** (Python 3.11 or newer):

```bash
python -m pip install -r requirements.txt
python -m pytest tests -v
```

| Test file | What it covers |
|---|---|
| `tests/logic_test.py` | LogicManager business rules: risk levels, escalation of previously flagged numbers, indicator checks, AI output validation |
| `tests/test_ai_analyzers.py` | Gemini analyzer with a mocked API (valid, wrapped, malformed and incomplete responses, API failure and retry), fallback AI model, AiManager, and the full AI -> logic -> storage pipeline |
| `tests/test_data_manager.py` | DataManager, JSON storage recovery (missing, empty, corrupt and wrongly formatted files), RecordConverter validation and summary statistics |

# Continuous Integration

`.github/workflows/tests.yml` runs on every push and pull request. It runs the test suite with Python 3.11, then builds the Docker image and runs the same tests inside the container. Results are shown in the **Actions** tab on GitHub and as a check on each pull request.
