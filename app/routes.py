import os
from flask import render_template, request, session, abort, redirect, send_from_directory, url_for
from . import flask_app, analysis_service, ocr, ALLOWED_TYPES, MAX_UPLOAD_BYTES, MIN_UPLOAD_BYTES, UPLOAD_FOLDER
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

@flask_app.route("/history/<int:record_id>")
def record_detail(record_id):
    record = analysis_service.get_record_by_id(record_id)

    if record is None:
        abort(404)

    return render_template(
        "results.html",
        result=record,
        saved=None,
        is_history_detail=True,
    )
    
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

# Show the upload form, and save the image when it is submitted.
@flask_app.route("/screenshot", methods=["GET", "POST"])
def screenshot_page():
    """Show the upload form, and save the image when it is submitted."""
    if request.method == "GET":
        return render_template("screenshot.html")

    file = request.files.get("file")
    if file is None or file.filename == "":
        return render_template("screenshot.html", error="Please choose an image.")

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_TYPES:
        return render_template("screenshot.html", error="Please upload a PNG or JPG image.")

    file.seek(0, os.SEEK_END)   # jump to the end of the file...
    size = file.tell()          # ...the position there is the size in bytes
    file.seek(0)                # go back to the start so it can be saved
    if size > MAX_UPLOAD_BYTES:
        return render_template("screenshot.html", error="That file is too large. Please choose an image under 5 MB.")
    if size < MIN_UPLOAD_BYTES:
        return render_template("screenshot.html", error="That file is too small to be a screenshot.")

    # A random name, so two users never overwrite each other's file
    filename = os.urandom(16).hex() + extension
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return redirect(url_for("crop_page", filename=filename))

# Send the uploaded image to the browser so Cropper.js can show it.
@flask_app.route("/screenshot/image/<filename>")
def uploaded_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Show the two croppers, then read the text from both boxes.
@flask_app.route("/screenshot/crop/<filename>", methods=["GET", "POST"])
def crop_page(filename):
    filename = os.path.basename(filename)    # keep only the file name, blocks names like "..\\secret"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.isfile(image_path):
        abort(404)

    if request.method == "GET":
        return render_template("crop.html", filename=filename)

    try:
        phone_box = _read_box(request.form, "1")
        message_box = _read_box(request.form, "2")
    except (KeyError, ValueError):
        return render_template("crop.html", filename=filename,
                               error="Please draw both crop boxes and try again.")

    try:
        phone = ocr.read_area(image_path, *phone_box)
        message = ocr.read_area(image_path, *message_box)
    finally:
        os.remove(image_path)   # Delete screenshots

    error = None
    if not phone and not message:
        error = "No text could be read. Try cropping again more tightly, or type it in below."

    # Show the Scanner page with the text filled in so the user can check it and press "Analyse Message" as normal.
    return render_template("scanner.html", ocr_phone=phone, ocr_message=message,
                           from_screenshot=True, error=error)

# Flask raises 413 when an upload is bigger than MAX_CONTENT_LENGTH
@flask_app.errorhandler(413)
def file_too_large(error):
    return render_template("screenshot.html", error="That file is too large. Please choose an image under 5 MB."), 413

# Get (x, y, width, height) for crop box 1 or 2 from the submitted form.
def _read_box(form, number):
    return tuple(int(float(form[name + number])) for name in ("x", "y", "width", "height"))