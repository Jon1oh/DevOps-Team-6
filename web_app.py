
from flask import Flask, render_template, request, session
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import secrets
import time

# Load environment variables BEFORE creating managers
load_dotenv(Path(__file__).resolve().parent / ".env")

# Import existing OOP components
from managers.ai_manager import AiManager
from managers.data_manager import DataManager
from managers.logic_manager import LogicManager
from storage.json_record_storage import JsonRecordStorage
from storage.record_converter import RecordConverter
from models.record import Record


app = Flask(__name__)

# Secret key for Flask sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Initialise existing OOP components
ai_manager = AiManager()
data_manager = DataManager(JsonRecordStorage())
logic_manager = LogicManager()

# Temporary server-side storage for pending fallback scans
# The session only stores a random token, not the original message.
pending_scans = {}

# Pending scans expire after 15 minutes
PENDING_SCAN_TIMEOUT = 900


def get_field(record, field, default=""):
    """Read a field from either a dictionary or Record object."""
    if isinstance(record, dict):
        return record.get(field, default)

    return getattr(record, field, default)


def record_to_dict(record):
    """Convert a Record into a dictionary for the website."""
    if isinstance(record, dict):
        result = record.copy()
    else:
        result = RecordConverter.to_dict(record)

    # Support both website and JSON storage message keys
    if "message" not in result:
        result["message"] = result.get("message_content", "")

    return result


def clean_expired_scans():
    """Remove pending scans older than 15 minutes."""
    current_time = time.time()

    expired_tokens = [
        token
        for token, scan in pending_scans.items()
        if current_time - scan["created_at"] > PENDING_SCAN_TIMEOUT
    ]

    for token in expired_tokens:
        pending_scans.pop(token, None)


def finish_analysis(ai_output):
    """Validate, process, escalate and save AI analysis."""

    # Validate AI output
    if not logic_manager.check_ai_output(ai_output):
        return render_template(
            "scanner.html",
            error="The AI returned an invalid analysis."
        )

    # Format and validate risk assessment
    ai_output = logic_manager.format_ai_output(ai_output)

    ai_output = logic_manager.validate_risk_assessment(
        ai_output
    )

    # Escalate risk based on previous flagged records
    flagged_records = data_manager.count_risk_levels(
        ai_output.phone_number
    )

    ai_output = logic_manager.escalate_flagged_number(
        ai_output,
        flagged_records
    )

    # Save the analysis
    saved, save_message = data_manager.save_record(
        RecordConverter.to_dict(ai_output)
    )

    # Convert result into dictionary for website
    result = record_to_dict(ai_output)

    return render_template(
        "results.html",
        result=result,
        saved=saved,
        save_message=save_message
    )


@app.route("/")
def dashboard():
    records = data_manager.records

    total = len(records)
    high = 0
    medium = 0
    low = 0

    for record in records:
        risk = str(get_field(record, "risk_level")).upper()

        if risk == "HIGH":
            high += 1
        elif risk == "MEDIUM":
            medium += 1
        elif risk == "LOW":
            low += 1

    statistics = {
        "total": total,
        "high": high,
        "medium": medium,
        "low": low
    }

    recent_records = [
        record_to_dict(record)
        for record in records[-5:][::-1]
    ]

    return render_template(
        "dashboard.html",
        statistics=statistics,
        recent_records=recent_records
    )


@app.route("/scanner", methods=["GET", "POST"])
def scanner():

    if request.method == "POST":

        clean_expired_scans()

        # ==========================================
        # CHECK USER'S FALLBACK AI DECISION
        # ==========================================

        fallback_choice = request.form.get("fallback_choice")

        if fallback_choice:

            token = session.pop("pending_scan_token", None)

            scan_data = pending_scans.pop(token, None) if token else None

            if scan_data is None:
                return render_template(
                    "scanner.html",
                    error=(
                        "Your pending scan has expired or is no longer "
                        "available. Please submit your message again."
                    )
                )

            # User declines fallback AI
            if fallback_choice == "no":
                return render_template(
                    "scanner.html",
                    error="Fallback analysis cancelled. You can try again later."
                )

            # User accepts fallback AI
            if fallback_choice == "yes":

                try:
                    record = Record(
                        timestamp=datetime.now().isoformat(),
                        phone_number=scan_data["phone_number"],
                        country_code=scan_data["country_code"],
                        message=scan_data["message"]
                    )

                    fallback_analyzer = (
                        ai_manager.get_fallback_analyzer()
                    )

                    ai_output = fallback_analyzer.analyze_message(
                        record
                    )

                    app.logger.info(
                        "Fallback AI analysis completed successfully."
                    )

                    return finish_analysis(ai_output)

                except Exception as error:
                    app.logger.exception(
                        "Fallback AI analysis failed."
                    )

                    return render_template(
                        "scanner.html",
                        error=f"Fallback AI analysis failed: {str(error)}"
                    )

            return render_template(
                "scanner.html",
                error="Invalid fallback selection."
            )

        # ==========================================
        # INITIAL MESSAGE SUBMISSION
        # ==========================================

        phone_number = request.form.get(
            "phone_number", ""
        ).strip()

        message = request.form.get(
            "message", ""
        ).strip()

        if not phone_number or not message:
            return render_template(
                "scanner.html",
                error="Please enter both a phone number and message."
            )

        try:
            # Split phone number and country code
            local_number, country_code = (
                logic_manager.split_country_code_phone_number(
                    phone_number
                )
            )

            # Create the input Record
            record = Record(
                timestamp=datetime.now().isoformat(),
                phone_number=local_number,
                country_code=country_code,
                message=message
            )

            # ==========================================
            # PRIMARY GEMINI AI ANALYSIS
            # ==========================================

            analyzer = ai_manager.get_analyzer()

            try:
                ai_output = analyzer.analyze_message(record)

            except Exception as error:
                app.logger.warning(
                    f"Gemini AI failed: {error}"
                )

                ai_output = False

            # ==========================================
            # ASK USER BEFORE USING FALLBACK AI
            # ==========================================

            if ai_output is False or ai_output is None:

                token = secrets.token_urlsafe(32)

                # Store original scan information on the server
                pending_scans[token] = {
                    "phone_number": local_number,
                    "country_code": country_code,
                    "message": message,
                    "created_at": time.time()
                }

                # Store only the random token in the session
                session["pending_scan_token"] = token

                return render_template(
                    "scanner.html",
                    fallback_prompt=True,
                    original_phone_number=phone_number,
                    original_message=message
                )

            # ==========================================
            # NORMAL GEMINI ANALYSIS RESULTS
            # ==========================================

            return finish_analysis(ai_output)

        except Exception as error:
            app.logger.exception("Message analysis failed")

            return render_template(
                "scanner.html",
                error=f"Analysis failed: {str(error)}"
            )

    return render_template("scanner.html")


@app.route("/history")
def history():

    records = [
        record_to_dict(record)
        for record in data_manager.records
    ]

    records.reverse()

    return render_template(
        "history.html",
        records=records
    )


if __name__ == "__main__":
    app.run(debug=True)
