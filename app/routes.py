from flask import render_template, request, session
from . import flask_app, analysis_service
from .utils import handle_fallback_choice, save_pending_scan, render_result, clean_expired_scans
from .models.record import Record
from datetime import datetime

@flask_app.route("/")
def dashboard():
    data = analysis_service.get_dashboard_data()
    return render_template("dashboard.html", statistics=data["statistics"], recent_records=data["recent_records"])

@flask_app.route("/history")
def history():
    records = analysis_service.get_history_records()
    return render_template("history.html", records=records)

@flask_app.route("/scanner", methods=["GET", "POST"])
def scanner():
    if request.method == "GET":
        return render_template("scanner.html")
 
    clean_expired_scans()
    fallback_choice = request.form.get("fallback_choice") # check user's fallback AI option
    if fallback_choice:
        return handle_fallback_choice(fallback_choice)
 
    # initial message submission
    phone_number = request.form.get("phone_number", "").strip()
    message = request.form.get("message", "").strip()
    
    if not phone_number or not message:
        return render_template("scanner.html", error="Please enter both a phone number and message.")
    record = Record(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        phone_number=phone_number,
        message=message
    )
    result = analysis_service.analyze_record(record)
    # prompt user before using fallback AI
    if result["status"] == "fallback_required":
        session["pending_scan_token"] = save_pending_scan(record) # the session only holds a random token
        return render_template("scanner.html", fallback_prompt=True, original_phone_number=phone_number, original_message=message)
 
    return render_result(result)