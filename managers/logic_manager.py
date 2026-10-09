import phonenumbers

# Determine risk_level value based on scam_probability number
def calculate_risk_level(probability):
    if probability >= 80:
        return "HIGH"
    elif probability >= 50:
        return "MEDIUM"
    else:
        return "LOW"
    

# Compare AI's risk level of message against our own logic of calculating risk level. In case AI gives inconsistent risk levels.
def validate_risk_level_from_ai(ai_output):
    expected = calculate_risk_level(ai_output["scam_probability"])
    
    if ai_output["risk_level"] != expected:
        ai_output["risk_level"] = expected # Ensure risk_level is one of the expected values
        
    return ai_output


# Escalates Risk Level to HIGH if Phone Number was previously involved in a High Risk Incident
# Function should take in a records dictionary that states the different risk levels associated with the phone number
# e.g., records = {"HIGH": 1, "MEDIUM": 0, "LOW": 0}
def escalate_flagged_number(ai_output, records):
    if records["HIGH"] > 0:
        ai_output["risk_level"] = "HIGH"
        message = f"{ai_output['phone_number']} was found in {records['HIGH']} High Risk Incidents."
        ai_output["indicators"].append(message)
    return ai_output


# check if phone_number field from AI output still contains a country code. If yes, remove it and only keep the number. Else, return the number. There is no spacing between the country code and number
# check if the country_code field is an empty string or not. If yes, extract the country code from the phone number
def check_country_code_in_phone_number(ai_output):
    phone_number = ai_output["phone_number"]
    country_code = ai_output["country_code"]
    
    if phone_number.startswith(country_code):
        ai_output["phone_number"] = phone_number[len(country_code):] # Ensure phone_number does not contain country code
            
    return ai_output


def split_country_code_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        country_code = f"+{parsed_number.country_code}"
        local_number = str(parsed_number.national_number)
        return local_number, country_code

    except phonenumbers.NumberParseException:
        return phone_number, ""

# check scam indicators based on risk level of the analyzed message
def validate_scam_indicators(ai_output):
    if ai_output["risk_level"] in ["HIGH", "MEDIUM"]:
        if len(ai_output["indicators"]) == 0: # when the analyzed message is potentially a scam but there aren't any indicators
            return False
    elif len(ai_output["indicators"]) == 0 : # when the risk_level is LOW, the indicators list can be empty
        ai_output["indicators"] = "NIL" # assign a readable value to indicators if risk_level is low and list is empty
    
    return ai_output
    
# Ensure the AI output contains all required fields and fields are not empty. If any field or value is missing or invalid, return False. Otherwise, return True.
def check_ai_output(ai_output):
    required_fields = {
        "timestamp": str,
        "phone_number": str,
        "country_code": str,
        "message_content": str,
        "scam_probability": int,
        "risk_level": str,
        "scam_type": str,
        "indicators": list,
        "explanation": str,
        "recommendation": str
    }
        
    # Validate field values
    for field in required_fields:
         # Ensure all required fields are present in the AI output. Else, return False
        if field not in ai_output:
            return False
        
        value = ai_output[field]      
        
        # Type Validation as per required_fields
        if not isinstance(value, required_fields[field]):
            return False
        
        # Strings must not be empty  
        if isinstance(value, str) and not value.strip():
            return False
        
        # Lists must exist, but may be empty (for safe messages)
        if field == "indicators" and not isinstance(value, list):
            return False
            
        # No field value should be None
        if value is None:
            return False
    
    # Ensure scam_probability is a number between 0 and 100. Else, return False
    if not 0 <= ai_output["scam_probability"] <= 100:
        return False
    
    return True

# Our Backup AI will return scam_type with an underscore ("_") instead of spacing
# Function will remove that underscore and capitalize the first letter of each word for display
def format_scam_type(ai_output):
    if "_" in ai_output["scam_type"]: # for backup AI output
        scam_type = ai_output["scam_type"].replace("_", " ").split() # Replaces underscore (_) with a space and splits it
        ai_output["scam_type"] = scam_type.title() # capitalize the first letter of each word
    else: # for AI API output
        ai_output["scam_type"] = ai_output["scam_type"].title()
    return ai_output

# Ensure data in all fields are in the correct format.
def format_ai_output(ai_output):
    # Ensure risk_level is one of the expected values
    validate_risk_level_from_ai(ai_output)
    
    # Ensure phone_number does not contain country code
    check_country_code_in_phone_number(ai_output)
    
    # Display scam_type with no underscore
    format_scam_type(ai_output)
    
    return ai_output