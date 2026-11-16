# logic_test.py is an automated test script that tests the functions in the LogicManager class.
# For Running Locally (run it in the root directory): python -m pytest .\tests\logic_test.py
# For Running on Docker Image: docker run --rm ai_scam_detector pytest test/logic_test.py -v

import pytest
from managers.logic_manager import LogicManager
from app.models.record import Record

# Setting up our environment - ai_output() will be ran for every function that needs it and will be reset once the function ends
@pytest.fixture
def ai_output():
    record_id = None
    timestamp = "2026-09-18 14:30:00"
    phone_number = "4155550123"
    country_code = "+1"
    message = "Your parcel is waiting for delivery. Please confirm delivery address by clicking the link below: http://sh0ppedelivery.com"
    scam_probability = 72
    risk_level = "MEDIUM"
    scam_type = "Delivery Scam"
    indicators = ["Overseas phone number", "Unexpected delivery notification", "Suspicious link", "Requests personal information"]
    explanation = "The message comes from an overseas number and requests the recipient's delivery information through a suspicious link."
    recommendation = "Do not click the link or provide your address or personal information. Check your parcel status through the courier's official website or application."
    ai_output = Record(record_id, timestamp, phone_number, country_code, message, scam_probability, risk_level, scam_type, indicators, explanation, recommendation)
    return ai_output

# Test Cases for test_check_ai_output function
@pytest.mark.parametrize("field, value, expected", [
    # Test for Correct Data Type - True Cases
    ("timestamp", "2026-09-18 14:30:00", True),
    ("phone_number", "97368263", True),
    ("country_code", "+65", True),
    ("message", "Your parcel is waiting for delivery. Please confirm delivery address by clicking the link below: http://sh0ppedelivery.com", True),
    ("scam_probability", 50, True),
    ("indicators", [], True),
    ("explanation", "The message comes from an overseas number and requests the recipient's delivery information through a suspicious link.", True),
    ("recommendation", "Do not click the link or provide your address or personal information. Check your parcel status through the courier's official website or application.", True),
    
    # Test for Correct Data Type - False Cases
    ("timestamp", 202609181700, False),             # Should be str
    ("phone_number", 97263847, False),              # Should be str
    ("country_code", 65, False),                    # Should be str
    ("message", None, False),                       # Should be str
    ("scam_probability", "60", False),              # Should be int
    ("indicators", "Suspicious Link", False),       # Should be list
    ("explanation", None, False),                   # Should be str
    ("recommendation", 1, False),                   # Should be str
    
    # Test for Empty Strings
    ("timestamp", "", False),
    ("phone_number", "", False),
    ("country_code", "", False),
    ("message", "", False),
    ("explanation", "", False),
    ("recommendation", "", False),
    
    # Test for Scam Probability within 0-100 Range
    ("scam_probability", -1, False),
    ("scam_probability", 101, False),
    ("scam_probability", 100, True),
    ("scam_probability", 0, True),
    
    # Test for Risk Level within (HIGH, MEDIUM, or LOW)
    ("risk_level", "None", False),
    ("risk_level", "HIGH", True),
    ("risk_level", "MEDIUM", True),
    ("risk_level", "LOW", True)
])

# Verify that ai_output is valid (correct values, data type, scores)
def test_check_ai_output(ai_output, field, value, expected):
    setattr(ai_output, field, value)
    assert LogicManager().check_ai_output(ai_output) == expected

# Test Cases for - test_validate_risk_level function
@pytest.mark.parametrize(
    # Test whether the scam_probability scores match the appropriate risk_level labels
    # 80-100: HIGH, 50-79: MEDIUM, 0-49: LOW
    
    "probability, risk_level, expected_result",
    [   # True Cases
        (90, "HIGH", "HIGH"),
        (72, "MEDIUM", "MEDIUM"),
        (20, "LOW", "LOW"),
        
        # False Cases
        (20, "HIGH", "LOW"),
        (20, "MEDIUM", "LOW"),
        (49, "LOW", "LOW"),         # Boundary Test for Low
        (72, "LOW", "MEDIUM"),      
        (72, "HIGH", "MEDIUM"),
        (50, "MEDIUM", "MEDIUM"),   # Boundary Test for Medium
        (79, "MEDIUM", "MEDIUM"),   # Boundary Test for Medium
        (85, "MEDIUM", "HIGH"),
        (85, "LOW", "HIGH"),
        (100, "MEDIUM", "HIGH"),    # Boundary Test for High
        (80, "LOW", "HIGH")         # Boundary Test for High
    ]
)

# Verifies whether Logic will change inconsistent risk results from AI
def test_validate_risk_level(ai_output, probability, risk_level, expected_result):
    ai_output.scam_probability = probability
    ai_output.risk_level = risk_level

    result = LogicManager()._validate_risk_level(ai_output)

    assert result.risk_level == expected_result

# Test Cases for - test_validate_scam_indicators function
@pytest.mark.parametrize (
    # HIGH or MEDIUM need to have at least 1 indicator
    # If HIGH or MEDIUM don't have any indicators, they are changed to LOW
    # If LOW has no indicators, "NIL" will be appended to prevent displaying an empty list
    
    "risk_level, indicators, expected_result",
    [   
        # True Cases
        ("HIGH",   ["Suspicious links", "Requests for money"], ["Suspicious links", "Requests for money"]), # Valid Case
        ("MEDIUM", ["Urgency or pressure tactics"],            ["Urgency or pressure tactics"]),
        ("LOW",    ["Suspicious links"],                       ["Suspicious links"]),
        
        # HIGH or MEDIUM need to have at least 1 indicator
        ("HIGH",   [],                                         ["NIL"]),
        ("MEDIUM", [],                                         ["NIL"]),
        ("LOW",    [],                                         ["NIL"]), # "NIL" is assigned to empty lists when LOW
    ],
)

# Validates if Scam Indicators was presented properly
def test_validate_scam_indicators(ai_output, risk_level, indicators, expected_result):
    ai_output.risk_level = risk_level
    ai_output.indicators = indicators
    ai_output = LogicManager()._validate_scam_indicators(ai_output)
    
    if expected_result == False:
        assert ai_output == False
    else:
        assert ai_output.indicators == expected_result

# Test Cases for - test_validate_scam_probability function
@pytest.mark.parametrize(
    # If risk_level is LOW and scam_probability does not match the range of 0-49, we will assign scam_probability to 49
    "risk_level, scam_probability, expected_result",
    [   
        # Normal Cases - Nothing should be changed
        ("LOW", 49, 49),
        ("LOW", 0, 0),
        ("LOW", 30, 30),
        
        # Changed Cases - Scam Probability score is changed to 49
        ("LOW", 80, 49),
        ("LOW", 50, 49)
    ]   
)

# Validate AI's Scam Probability Score
def test_validate_scam_probability(ai_output, risk_level, scam_probability, expected_result):
    ai_output.risk_level = risk_level
    ai_output.scam_probability = scam_probability
    ai_output = LogicManager()._validate_scam_probability(ai_output)
    assert ai_output.scam_probability == expected_result

# Test Cases for - test_check_country_code_in_phone_number function
@pytest.mark.parametrize(
    "phone_number, country_code, expected_phone_number",
    [
        # Code attached with a +
        ("+6591234567",    "+65",  "91234567"),      # Singapore
        ("+14155550123",   "+1",   "4155550123"),    # United States
        ("+16045550123",   "+1",   "6045550123"),    # Canada (also +1)
        ("+447700900123",  "+44",  "7700900123"),    # United Kingdom
        ("+61412345678",   "+61",  "412345678"),     # Australia
        ("+64211234567",   "+64",  "211234567"),     # New Zealand
        ("+60123456789",   "+60",  "123456789"),     # Malaysia
        ("+6281234567890", "+62",  "81234567890"),   # Indonesia
        ("+639171234567",  "+63",  "9171234567"),    # Philippines
        ("+66812345678",   "+66",  "812345678"),     # Thailand
        ("+84912345678",   "+84",  "912345678"),     # Vietnam
        ("+919876543210",  "+91",  "9876543210"),    # India
        ("+819012345678",  "+81",  "9012345678"),    # Japan
        ("+821012345678",  "+82",  "1012345678"),    # South Korea
        ("+8613812345678", "+86",  "13812345678"),   # China
        ("+4915123456789", "+49",  "15123456789"),   # Germany
        ("+33612345678",   "+33",  "612345678"),     # France
        ("+5511912345678", "+55",  "11912345678"),   # Brazil
        ("+27821234567",   "+27",  "821234567"),     # South Africa

        # 3-digit country codes
        ("+85291234567",   "+852", "91234567"),      # Hong Kong
        ("+971501234567",  "+971", "501234567"),     # United Arab Emirates
        ("+2348012345678", "+234", "8012345678"),    # Nigeria

        # No + on either field
        ("6591234567",     "65",   "91234567"),
        ("447700900123",   "44",   "7700900123"),
        ("971501234567",   "971",  "501234567"),

        # Already stripped: nothing to remove
        ("91234567",       "65",   "91234567"),
        ("7700900123",     "44",   "7700900123"),
        ("501234567",      "971",  "501234567")
    ]
)    

# Validate if Country Code was removed
def test_remove_country_code_in_phone_number(ai_output, phone_number, country_code, expected_phone_number):
    ai_output.phone_number = phone_number
    ai_output.country_code = country_code
    ai_output = LogicManager().remove_country_code_in_phone_number(ai_output)
    
    assert ai_output.phone_number == expected_phone_number
    assert ai_output.country_code == country_code

# Test Cases for - test_split_country_code_phone_number function
@pytest.mark.parametrize(
    "phone_number, expected_local, expected_code",
    [
        # Valid international numbers: split into local number and country code
        ("+6591234567", "91234567", "+65"),        # Singapore
        ("+14155550123", "4155550123", "+1"),      # US
        ("+447911123456", "7911123456", "+44"),    # UK
        ("+60123456789", "123456789", "+60"),      # Malaysia

        # Cannot be parsed: number comes back unchanged with an empty country code
        ("91234567", "91234567", ""),              # no "+" and no region
        ("abc", "abc", ""),                        # not a number
        ("", "", ""),                              # empty string
    ],
)

# This function splits a full international phone number (like +6591234567) into its local number and country code, and falls back gracefully if it can’t.
def test_split_country_code_phone_number(phone_number, expected_local, expected_code):
    local_number, country_code = LogicManager().split_country_code_phone_number(phone_number)
    assert local_number == expected_local
    assert country_code == expected_code

# Test Cases for - test_escalate_flagged_number function
@pytest.mark.parametrize(
    "risk_level, records, expected_result",
    [
        ("LOW",    {"HIGH": 2, "MEDIUM": 0, "LOW": 0}, "HIGH"), # Escalated Example
        ("LOW",    {"HIGH": 1, "MEDIUM": 0, "LOW": 0}, "HIGH"),
        ("MEDIUM", {"HIGH": 0, "MEDIUM": 1, "LOW": 0}, "MEDIUM"), # Non-Escalated Example
        ("LOW",    {"HIGH": 0, "MEDIUM": 0, "LOW": 1}, "LOW"),
        ("LOW",    {"HIGH": 1, "MEDIUM": 1, "LOW": 1}, "HIGH"),
        ("HIGH",    {"HIGH": 0, "MEDIUM": 0, "LOW": 0}, "HIGH"), # Phone Number not found before
        ("LOW",    {"HIGH": 0, "MEDIUM": 0, "LOW": 0}, "LOW"),
        ("MEDIUM",    {"HIGH": 0, "MEDIUM": 0, "LOW": 0}, "MEDIUM")
    ]
)

# Verifies if risk_level will change when phone number has been flagged previously
def test_escalate_flagged_number(ai_output, risk_level, records, expected_result):
    ai_output.risk_level = risk_level
    ai_output = LogicManager().escalate_flagged_number(ai_output, records)
    assert ai_output.risk_level == expected_result