# LogicManager will ensure whatever reaches the user is valid, consistent, and trustworthy.
import phonenumbers
from record import Record
class LogicManager():
    # Takes in Record class
    
    # Ensure the AI output contains all required fields and fields are not empty. If any field or value is missing or invalid, return False. Otherwise, return True.
    def check_ai_output(ai_output: Record):
        required_fields = {
            "record_id": type(None), # isinstance() only tests for None if we use type(None)
            "timestamp": str,
            "phone_number": str,
            "country_code": str,
            "message": str,
            "scam_probability": int,
            "risk_level": str,
            "scam_type": str,
            "indicators": list,
            "explanation": str,
            "recommendation": str
        }
        
        for field in required_fields:
            check_data_type = required_fields[field]
            value = getattr(ai_output, field) # gets the value for field in ai_output
            
            # Type validation for fields
            if not isinstance(value, check_data_type):
                print(value)
                print(check_data_type)
                return False
            
            # Strings must not be Empty
            if isinstance(value, str) and not value.strip():
                return False
        
        # Scam Probability is within 0-100 Range
        if not 0 <= ai_output.scam_probability <= 100:
                return False
            
        return True
    
    # Validates AI's Risk Level
    def validate_risk_level(ai_output: Record):
        # Calculate Risk Level off our own formula
        if ai_output.scam_probability >= 80 and ai_output.indicators != []:
            expected_risk_level = "HIGH"
        elif ai_output.scam_probability >= 50 and ai_output.indicators != []:
            expected_risk_level = "MEDIUM"
        else:
            expected_risk_level = "LOW"
        
        # Replace AI's Risk Level to ours if they are not the same
        if ai_output.risk_level != expected_risk_level:
            ai_output.risk_level = expected_risk_level
            
        return ai_output
            
    # check scam indicators based on risk level of the analyzed message
    def validate_scam_indicators(ai_output: Record):
        # If Risk Level is HIGH or MEDIUM but has no indicators, the Risk Level will be changed to LOW
        if ai_output.risk_level in ["HIGH", "MEDIUM"]:
            if len(ai_output.indicators) == 0 and ai_output.scam_probability >= 50: # when the analyzed message is potentially a scam but there aren't any indicators
                ai_output = LogicManager.validate_risk_level(ai_output) # Ensure Risk Level is correct
        
        # We assign a readable value to indicators if risk_level is low and list is empty
        if len(ai_output.indicators) == 0 and ai_output.risk_level == "LOW": # when the risk_level is LOW, the indicators list can be empty
            ai_output.indicators = ["NIL"] 
        
        return ai_output
    
    # Validates AI's Scam Probability Score
    def validate_scam_probability(ai_output: Record):
        # If Scam Probability Score does not match a Risk Level of "LOW", we will tweak the score such that it fits the range of "LOW"
        if ai_output.risk_level == "LOW" and ai_output.scam_probability > 49:
            ai_output.scam_probability = 49 # Give it the highest Scam Proabability Score within the range of "LOW"
        
        return ai_output
        
    # check if phone_number field from AI output still contains a country code. If yes, remove it and only keep the number.
    def check_country_code_in_phone_number(ai_output: Record):
        phone_number = ai_output.phone_number
        country_code = ai_output.country_code
        
        if phone_number.startswith(country_code):
            ai_output.phone_number = phone_number[len(country_code):] # Ensure phone_number does not contain country code
                
        return ai_output
    
    # This function splits a full international phone number (like +6591234567) into its local number and country code, and falls back gracefully if it can’t.
    def split_country_code_phone_number(phone_number):
        try:
            parsed_number = phonenumbers.parse(phone_number)
            country_code = f"+{parsed_number.country_code}"
            local_number = str(parsed_number.national_number)
            return local_number, country_code

        except phonenumbers.NumberParseException:
            return phone_number, ""
        
    # Escalates Risk Level to HIGH if Phone Number was previously involved in a High Risk Incident
    # Function should take in a records dictionary that states the different risk levels associated with the phone number
    # e.g., records = {"HIGH": 1, "MEDIUM": 0, "LOW": 0}
    def escalate_flagged_number(ai_output: Record, phone_records):
        if phone_records["HIGH"] > 0:
            indicator_list = ai_output.indicators # Indicator List grabbed from AI Output via Getter
            ai_output.risk_level = "HIGH"
            message = f"{ai_output.phone_number} was found in {phone_records['HIGH']} High Risk Incidents."
            indicator_list.append(message)
            ai_output.indicators = indicator_list # Set Indicator List after appending message
        return ai_output
        
    # Our Backup AI will return scam_type with an underscore ("_") instead of spacing
    # Function will remove that underscore and capitalize the first letter of each word for display
    def format_scam_type(ai_output: Record):
        if "_" in ai_output.scam_type: # for backup AI output
            scam_type = ai_output.scam_type.replace("_", " ").split() # Replaces underscore (_) with a space and splits it
            result = " ".join(word.capitalize() for word in scam_type)
            ai_output.scam_type = result
        else: # for AI API output
            ai_output.scam_type = ai_output.scam_type.title()
        return ai_output
    
    # Ensure data in all fields are in the correct format.
    def format_ai_output(ai_output):        
        # Ensure risk_level is one of the expected values
        LogicManager.validate_risk_level(ai_output)
        
        # Ensure phone_number does not contain country code
        LogicManager.check_country_code_in_phone_number(ai_output)
        
        # Display scam_type with no underscore
        LogicManager.format_scam_type(ai_output)
        
        return ai_output