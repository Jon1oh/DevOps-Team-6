# Ensure the AI output contains all required fields and fields are not empty. If any field or value is missing or invalid, return False. Otherwise, return True.
def check_ai_output(ai_output):
    required_fields = [
        "timestamp", # str
        "phone_number", # str
        "message_content", # str
        "scam_probability", # int
        "risk_level", # str 
        "scam_type", # str
        "indicators", # list
        "explanation", # str
        "recommendation" # str
    ]
    
    # Ensure all required fields are present in the AI output. Else, return False
    for field in required_fields:
        if field not in ai_output:
            return False
        
    # Ensure all fields are not empty
    for field in required_fields:
        value = ai_output[field]        
        if (type(value) is str) and (not value.strip()): # if the string value is empty
            return False
        elif (type(value) is list) and (not value): # if the list value is empty
            return False
        elif value is None:
            return False
                
    # Ensure scam_probability is a number between 0 and 100. Else, return False
    if not 0 <= ai_output["scam_probability"] <= 100:
        return False
    
    # Ensure risk_level is one of the expected values. Else, return False
    if ai_output["risk_level"] not in ["LOW", "MEDIUM", "HIGH"]:
        return False

    return True

# Determine risk_level value based on scam_probability number
# ? Should risk_level be determined by the AI API? (fully dependent on AI)
# * I feel calculate_risk_level in the logic manager is fine because it can validate the risk_level value returned from the AI API in case it is wrong.
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
        ai_output["risk_level"] = expected
        
    return ai_output

# Compares the Phone Number against past records
# Function should take in a records dictionary that states the different risk levels associated with the phone number
# e.g., records = {"HIGH": 1, "MEDIUM": 0, "LOW": 0}
def check_phone_number(ai_output, records):
    if records["HIGH"] > 0:
        ai_output["risk_level"] = "HIGH"
    return records