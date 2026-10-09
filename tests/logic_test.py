import pytest
import managers.logic_manager as lm

# Setting up our environment - ai_output() will be ran for every function that needs it and will be reset once the function ends
@pytest.fixture
def ai_output():
    ai_output = {
        "message_id": 5,
        "timestamp": "2026-09-18 14:30:00",
        "phone_number": "+14155550123",
        "country_code": "+1",
        "message_content": "Your parcel is waiting for delivery. Please confirm delivery address by clicking the link below: http://sh0ppedelivery.com",
        "scam_probability": 72,
        "risk_level": "MEDIUM",
        "scam_type": "Delivery/Parcel Scam",
        "indicators": [
            "Overseas phone number",
            "Unexpected delivery notification",
            "Suspicious link",
            "Requests personal information"
        ],
        "explanation": "The message comes from an overseas number and requests the recipient's delivery information through a suspicious link.",
        "recommendation": "Do not click the link or provide your address or personal information. Check your parcel status through the courier's official website or application."
    }
    return ai_output

# Test Cases for - test_calculate_risk_level function (e.g., Maps probability to 90, and expected to "HIGH")
@pytest.mark.parametrize("probability, expected", [
    (90, "HIGH"),
    (50, "MEDIUM"), # Boundary Test
    (80, "HIGH"), # Boundary Test
    (20, "LOW"),
    (0, "LOW"),
    (49, "LOW"),
    (79, "MEDIUM"),
    (100, "HIGH")
])

# Verifies that Risk Level Labels are correct
def test_calculate_risk_level(probability, expected):
    assert lm.calculate_risk_level(probability) == expected # asserts if the statement is true

# Test Cases for - test_validate_risk_level_from_ai function
@pytest.mark.parametrize(
    "probability, risk_level, expected_result",
    [
        (72, "MEDIUM", "MEDIUM"),
        (72, "LOW", "MEDIUM"),      # AI level too low
        (72, "HIGH", "MEDIUM"),     # AI level too high
        (85, "MEDIUM", "HIGH"),
        (20, "HIGH", "LOW"),
        (49, "MEDIUM", "LOW"),      # Boundary Test
        (50, "LOW", "MEDIUM"),
        (79, "HIGH", "MEDIUM"),
        (80, "MEDIUM", "HIGH"),
    ],
)

# Verifies whether Logic will change inconsistent risk results from AI
def test_validate_risk_level_from_ai(ai_output, probability, risk_level, expected_result):
    ai_output["scam_probability"] = probability
    ai_output["risk_level"] = risk_level

    result = lm.validate_risk_level_from_ai(ai_output)

    assert result["risk_level"] == expected_result

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
    ai_output["risk_level"] = risk_level
    ai_output = lm.escalate_flagged_number(ai_output, records)
    assert ai_output["risk_level"] == expected_result

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
def test_check_country_code_in_phone_number(ai_output, phone_number, country_code, expected_phone_number):
    ai_output["phone_number"] = phone_number
    ai_output["country_code"] = country_code
    ai_output = lm.check_country_code_in_phone_number(ai_output)
    
    assert ai_output["phone_number"] == expected_phone_number
    assert ai_output["country_code"] == country_code

# Test Cases for - test_validate_scam_indicators function
@pytest.mark.parametrize (
    "risk_level, indicators, expected_result",
    [
        ("HIGH",   ["Suspicious links", "Requests for money"], ["Suspicious links", "Requests for money"]), # Valid Case
        ("MEDIUM", ["Urgency or pressure tactics"],            ["Urgency or pressure tactics"]),
        ("LOW",    ["Suspicious links"],                       ["Suspicious links"]),
        ("HIGH",   [],                                         False), # HIGH or MEDIUM need to have at least 1 indicator
        ("MEDIUM", [],                                         False),
        ("LOW",    [],                                         "NIL"), # "NIL" is assigned to empty lists when LOW
    ],
)

# Validates if Scam Indicators was presented properly
def test_validate_scam_indicators(ai_output, risk_level, indicators, expected_result):
    ai_output["risk_level"] = risk_level
    ai_output["indicators"] = indicators
    ai_output = lm.validate_scam_indicators(ai_output)
    
    if expected_result == False:
        assert ai_output == False
    else:
        assert ai_output["indicators"] == expected_result

# Test Cases for test_check_ai_output function
@pytest.mark.parametrize("field, value, expected", [
    ("scam_probability", 0, True),
    ("scam_probability", 50, True),
    ("scam_probability", 100, True),
    ("indicators", [], True),
    ("recommendation", 1, False), # Wrong Data Type
    ("message_content", "", False), # Empty String
    ("indicators", "Suspicious link", False), 
    ("scam_probability", "None", False),
    ("scam_probability", -1, False), # Number not between 0 and 100
    ("scam_probability", 101, False)
])

# Verify that ai_output is not empty
def test_check_ai_output(ai_output, field, value, expected):
    ai_output[field] = value
    assert lm.check_ai_output(ai_output) == expected

# Test Cases for test_format_scam_type function
@pytest.mark.parametrize("value, expected", [
    ("impersonation scam", "Impersonation Scam"),
    ("phishing", "Phishing"),
    ("job_scam", "Job Scam"),
    ("Fake Website Scam", "Fake Website Scam"),
    ("fake subscription Scam", "Fake Subscription Scam"),
    ("delivery_parcel_scam", "Delivery Parcel Scam")
])

# Verifies that scam_type has no underscore (_)
def test_format_scam_type(ai_output, value, expected):
    ai_output["scam_type"] = value
    ai_output = lm.format_scam_type(ai_output)
    assert ai_output["scam_type"] == expected