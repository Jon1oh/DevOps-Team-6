"""Shared setup for all tests (loaded by pytest before any test file).

1. A placeholder Gemini API key is set if none exists, so the app can be
   imported on machines without a .env file (e.g. GitHub Actions). The tests
   never call the real API: Gemini is replaced by a fake client.
2. The app package is imported first. app/__init__.py imports the managers,
   and the managers import from app, so importing a manager first causes a
   circular import. Loading app first avoids it.
"""

import os

os.environ.setdefault("GEMINI_API_KEY", "placeholder-key-for-tests")

import app  # noqa: E402,F401  (must be imported before the managers)
