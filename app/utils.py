import secrets, time
from flask import render_template, session
from . import analysis_service

# Temporary server-side storage for pending fallback scans.
# The session only stores a random token, not the original message.
pending_scans = {}

# Pending scans expire after 15 minutes
PENDING_SCAN_TIMEOUT = 900


def save_pending_scan(phone_number, message):
    """Keep what the user typed on the server and return the random token for the session."""
    token = secrets.token_urlsafe(32)
    pending_scans[token] = {
        "phone_number": phone_number,
        "message": message,
        "created_at": time.time()
    }
    return token


def clean_expired_scans():
    """Remove pending scans older than 15 minutes."""
    current_time = time.time()
    expired_tokens = [
        token for token, scan in pending_scans.items()
        if current_time - scan["created_at"] > PENDING_SCAN_TIMEOUT
    ]
    for token in expired_tokens:
        pending_scans.pop(token, None)


def handle_fallback_choice(choice):
    """The user answered the 'use the fallback AI?' prompt."""
    token = session.pop("pending_scan_token", None)
    scan_data = pending_scans.pop(token, None) if token else None

    if scan_data is None:
        return render_template("scanner.html", error="Your pending scan has expired or is no longer available. Please submit your message again.")
    if choice == "no":
        return render_template("scanner.html", error="Fallback analysis cancelled. You can try again later.")
    if choice == "yes":
        return render_result(analysis_service.analyze_with_fallback_ai(scan_data["phone_number"], scan_data["message"]))

    return render_template("scanner.html", error="Invalid fallback selection.")


def render_result(result):
    """Turn the service's result dictionary into a page."""
    if result["status"] == "complete":
        return render_template("results.html", result=result["record"], saved=result["saved"], save_message=result["save_message"])
    return render_template("scanner.html", error=result["message"])