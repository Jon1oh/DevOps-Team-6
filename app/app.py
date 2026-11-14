import logging

class App:
    def __init__(self, ai_manager, data_manager, logic_manager, record_converter,io_manager):
        self._ai_manager = ai_manager
        self._data_manager = data_manager # records loaded on startup
        if self._data_manager.status_message: # when record does not load properly
            print(self._data_manager.status_message)
        else:
            print(f"Database Loaded: {len(self._data_manager.records)} records") 
        self.io_manager = io_manager
        self._logic_manager = logic_manager
        self._record_converter = record_converter
                    
    # analyze message with Gemini analyzer. If unavailable, use Fallback AI
    def analyze_record(self, record):
        # input validation
        try:
            record.phone_number, record.country_code = self.io_manager.split_number(record.phone_number)
        except ValueError:
            return {"status": "error", "message": "Enter a valid international phone number."}
        try:
            record.message = self.io_manager.parse_message(record.message)
        except ValueError:
            return {"status": "error", "message": "Enter a more meaningful message"}
        try:
            analyzer = self._ai_manager.get_analyzer()
            ai_output = analyzer.analyze_message(record)
        except Exception:
            logging.exception("Primary AI analysis failed.")
            return {"status": "fallback_required", "record": record}

        if ai_output is False or ai_output is None:
            return {"status": "fallback_required", "record": record}

        return self._process_ai_output(ai_output)

    # use the fallback AI analyzer if Gemini fails and the user chooses it
    def analyze_with_fallback_ai(self, record):
        try:
            analyzer = self._ai_manager.get_fallback_analyzer()
            ai_output = analyzer.analyze_message(record)
        except Exception as error:
            logging.exception("Fallback AI analysis failed.")
            return {"status": "error", "message": str(error)}

        if ai_output is False or ai_output is None:
            return {"status": "error", "message": "The fallback analyzer could not analyze this message."}

        return self._process_ai_output(ai_output)

    # validate and format the Gemini/Fallback AI output, then save the final record
    def _process_ai_output(self, ai_output):
        if not self._logic_manager.check_ai_output(ai_output):
            return {"status": "error", "message": "One of the fields in the AI output is invalid."}

        ai_output = self._logic_manager.format_ai_output(ai_output)
        ai_output = self._logic_manager.validate_risk_assessment(ai_output)
        flagged_records = self._data_manager.count_risk_levels(ai_output.phone_number)
        ai_output = self._logic_manager.escalate_flagged_number(ai_output, flagged_records)
        saved, save_message = self._data_manager.save_record(self._record_converter.to_dict(ai_output))

        return {
            "status": "complete",
            "record": ai_output,
            "saved": saved,
            "save_message": save_message,
        }
    
    # get data from data manager to display on the dashboard
    def get_dashboard_data(self):
        records = self._data_manager.records
        risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for record in records:
            risk = str(record.risk_level).upper()
            if risk in risk_counts:
                risk_counts[risk] += 1

        return {
            "statistics": {
                "total": len(records),
                "high": risk_counts["HIGH"],
                "medium": risk_counts["MEDIUM"],
                "low": risk_counts["LOW"],
            },
            "recent_records": records[-5:][::-1],
        }       

    # get the records from data manager in reverse order, starting with the newest record
    def get_history_records(self):
        return self._data_manager.records[::-1] 