from datetime import datetime
import secrets, time
import re
from flask import Blueprint, render_template, request, session
import phonenumbers
# Import your helpers and models
from app.models.record import Record

#this class handles all input validation and output of the application
class iomanager:
    def __init__(self,analysis_service):
        self.blueprint : Blueprint = Blueprint('io_manager', __name__)
        self.analysis_service = analysis_service
        self._register_routes()
        self.pending_scans = {}
        self.PENDING_SCAN_TIMEOUT = 900
        pass
    
    #this method handles routes
    def _register_routes(self) -> None:
        self.blueprint.add_url_rule('/', view_func=self.dashboard, methods=['GET'])
        self.blueprint.add_url_rule('/history', view_func=self.history, methods=['GET'])
        self.blueprint.add_url_rule('/scanner', view_func=self.scanner, methods=['GET', 'POST'])
    
    #this method handles
    def dashboard(self) -> str:
        data = self.analysis_service.get_dashboard_data()
        return render_template("dashboard.html", statistics=data["statistics"], recent_records=data["recent_records"])
    
    
    def history(self) -> str:
        records = self.analysis_service.get_history_records()
        return render_template("history.html", records=records)
    
    
    def scanner(self) ->str:
        if request.method == "GET":
            return render_template("scanner.html")
        self.clean_expired_scans()
        fallback_choice = request.form.get("fallback_choice") # check user's fallback AI option
        if fallback_choice:
            return self.handle_fallback_choice(fallback_choice)
        # initial message submission
        phone_number = request.form.get("phone_number", "").strip()
        message = request.form.get("message", "").strip()
        if not phone_number or not message:
            return render_template("scanner.html", error="Please enter both a phone number and message.")
        try:
            phone_number, country_code = self.split_number(phone_number)
        except ValueError:
            return render_template("scanner.html", error="Enter a valid international phone number.")
        try:
            message = self.parse_message(message)
        except ValueError:
            return render_template("scanner.html", error="Enter a more meaningful message.")
        record = Record(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            phone_number=phone_number,
            country_code=country_code,
            message=message
        )
        result = self.analysis_service.analyze_record(record)
        # prompt user before using fallback AI
        if result["status"] == "fallback_required":
            session["pending_scan_token"] = self.save_pending_scan(record) # the session only holds a random token
            return render_template("scanner.html", fallback_prompt=True, original_phone_number=phone_number, original_message=message)
        return self.render_result(result)
    
    
    def save_pending_scan(self,record):
        """Keep what the user typed on the server and return the random token for the session."""
        token = secrets.token_urlsafe(32)
        self.pending_scans[token] = {
            "record" : record,
            "created_at": time.time()
        }
        return token
    
    
    def clean_expired_scans(self):
        """Remove pending scans older than 15 minutes."""
        current_time = time.time()
        expired_tokens = [
            token for token, scan in self.pending_scans.items()
            if current_time - scan["created_at"] > self.PENDING_SCAN_TIMEOUT
        ]
        for token in expired_tokens:
            self.pending_scans.pop(token, None)
            
    
    def handle_fallback_choice(self,choice):
        """The user answered the 'use the fallback AI?' prompt."""
        token = session.pop("pending_scan_token", None)
        scan_data = self.pending_scans.pop(token, None) if token else None
        
        if scan_data is None:
            return render_template("scanner.html", error="Your pending scan has expired or is no longer available. Please submit your message again.")
        if choice == "no":
            return render_template("scanner.html", error="Message analysis cancelled. You can try again later.")
        if choice == "yes":
            record =scan_data["record"]
            return self.render_result(self.analysis_service.analyze_with_fallback_ai(record))

        return render_template("scanner.html", error="Invalid fallback selection.")    
    
    
    def render_result(self,result):
        """Turn the service's result dictionary into a page."""
        if result["status"] == "complete":
            return render_template("results.html", result=result["record"], saved=result["saved"], save_message=result["save_message"])
        return render_template("scanner.html", error=result["message"])
    
    #this method checks if the phone number is valid
    def validate_number(self,number:str)-> phonenumbers.PhoneNumber:
        if "+" not in number:
            number = "+" + number.replace(" ", "")
        try:
            parsed_number = phonenumbers.parse(number, None)
            print(parsed_number)
        except phonenumbers.NumberParseException as error:
            raise ValueError("Enter a valid international phone number.") from error
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("Enter a valid international phone number")
        return parsed_number
    
    #this method splits the phonenumber to country code and phone number
    def split_number(self,number:str) ->tuple[str,str]:
        parsed_number =self.validate_number(number)
        country_code = f"+{parsed_number.country_code}"
        local_number = str(parsed_number.national_number)
        return local_number, country_code 
            
    #this method is used to parse the message before it is sent to the ai
    def parse_message(self,message:str)->str:
        message = re.sub(r'\s+', ' ', message).strip()
        words = re.findall(r"[A-Za-z]+", message)
        total_letters = sum(len(word) for word in words)
        if total_letters >= 8:
            return message
        else:
            raise ValueError