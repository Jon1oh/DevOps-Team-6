
import joblib
import re
import json

MODEL_FILE = "scam_detection_model.pkl"


# ============================================================
# REQUIRED FIELDS FOR LOGIC MANAGER
# ============================================================

required_fields = {
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


# ============================================================
# LOAD COMBINED MODEL
# ============================================================

print("Loading scam detection model...")

model_data = joblib.load(MODEL_FILE)

spam_model = model_data["spam_model"]
spam_vectorizer = model_data["spam_vectorizer"]

scam_type_model = model_data["scam_type_model"]
scam_vectorizer = model_data["scam_vectorizer"]

print("Model loaded successfully.")


# ============================================================
# DETECT SCAM INDICATORS
# ============================================================

def detect_indicators(message):
    indicators = []
    message_lower = message.lower()

    # 1. Unexpected prize
    prize_words = [
        "won", "winner", "prize", "reward",
        "congratulations", "cash prize",
        "lucky draw", "claim"
    ]

    if any(word in message_lower for word in prize_words):
        indicators.append("Unexpected prize claim")

    # 2. Suspicious link
    if re.search(r"https?://", message_lower):
        indicators.append("Suspicious link")

    # 3. Large financial reward
    if re.search(r"\$\s?\d{1,3}(?:,\d{3})+", message):
        indicators.append("Large financial reward")

    # 4. Spelling mistakes / suspicious characters
    suspicious_patterns = [
        r"congratulat0ns",
        r"cl@im",
        r"w1n",
        r"fr33",
        r"pr1ze",
        r"acc0unt"
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, message_lower):
            indicators.append("Spelling mistakes")
            break

    # 5. Urgent language
    urgency_words = [
        "urgent", "immediately", "act now",
        "last chance", "within 24 hours"
    ]

    if any(word in message_lower for word in urgency_words):
        indicators.append("Urgent or threatening language")

    # 6. Account verification
    verification_words = [
        "verify your account",
        "verify your identity",
        "account suspended",
        "account locked"
    ]

    if any(word in message_lower for word in verification_words):
        indicators.append("Requests account verification")

    # 7. Personal information
    personal_information_words = [
        "password", "otp", "one-time password",
        "credit card", "card number", "nric",
        "personal information"
    ]

    if any(word in message_lower for word in personal_information_words):
        indicators.append("Requests sensitive personal information")

    # 8. Payment / money transfer
    payment_words = [
        "transfer money", "send money",
        "bank transfer", "payment", "pay now", "deposit"
    ]

    if any(word in message_lower for word in payment_words):
        indicators.append("Requests payment or money transfer")

    if len(indicators) == 0:
        indicators.append("No obvious scam indicators detected")

    return indicators


# ============================================================
# GENERATE EXPLANATION
# ============================================================

def generate_explanation(scam_type, indicators):

    if scam_type == "Prize Scam":
        if (
            "Unexpected prize claim" in indicators
            and "Large financial reward" in indicators
        ):
            return (
                "The message claims that the recipient has won "
                "a large prize without any prior participation. "
                "It also contains a suspicious link and may use "
                "spelling mistakes or unusual characters to make "
                "the message appear convincing."
            )

        return (
            "The message claims that the recipient has won "
            "a prize or reward and contains characteristics "
            "commonly associated with prize scams."
        )

    if scam_type == "Banking Scam":
        return (
            "The message contains banking-related language "
            "and may attempt to make the recipient verify an "
            "account, provide sensitive information, or take "
            "immediate action."
        )

    if scam_type == "Phishing Scam":
        return (
            "The message appears to be attempting to obtain "
            "sensitive information by directing the recipient "
            "to verify an account or follow a suspicious link."
        )

    if scam_type == "Investment Scam":
        return (
            "The message promotes a financial opportunity or "
            "investment and may attempt to persuade the recipient "
            "to provide money or personal information."
        )

    if scam_type == "Job Scam":
        return (
            "The message appears to offer a job or income "
            "opportunity and may contain suspicious requests "
            "for payment or personal information."
        )

    if scam_type == "Loan Scam":
        return (
            "The message appears to promote a loan or financial "
            "service and may request personal information, "
            "payments, or other sensitive details."
        )

    return (
        "The message contains characteristics that are "
        "commonly associated with scam messages. The detected "
        "indicators suggest that the recipient should exercise "
        "caution before responding or following any instructions."
    )


# ============================================================
# GENERATE RECOMMENDATION
# ============================================================

def generate_recommendation(risk_level):

    if risk_level == "HIGH":
        return (
            "Do not click the link or provide personal information. "
            "Do not transfer money. Verify the message through the "
            "organisation's official website and report the message "
            "as suspicious."
        )

    elif risk_level == "MEDIUM":
        return (
            "Be cautious with this message. Do not click suspicious "
            "links or provide personal information until the sender "
            "has been verified through an official source."
        )

    else:
        return (
            "The message does not appear highly suspicious based "
            "on the current model prediction. However, remain "
            "cautious and verify unexpected requests before taking action."
        )


# ============================================================
# DETERMINE RISK LEVEL
# ============================================================

def get_risk_level(scam_probability):

    if scam_probability >= 80:
        return "HIGH"

    elif scam_probability >= 50:
        return "MEDIUM"

    else:
        return "LOW"


# ============================================================
# ANALYSE MESSAGE
# ============================================================

def analyse_message(message, phone_number, country_code):

    # STEP 1: HAM / SPAM MODEL
    message_vector = spam_vectorizer.transform([message])
    prediction = spam_model.predict(message_vector)[0]
    probabilities = spam_model.predict_proba(message_vector)[0]
    class_probabilities = dict(
        zip(spam_model.classes_, probabilities)
    )

    spam_probability = class_probabilities.get("spam", 0)
    scam_probability = round(spam_probability * 100)

    # STEP 2: RISK LEVEL
    risk_level = get_risk_level(scam_probability)

    # STEP 3: SCAM TYPE
    if prediction == "spam":
        scam_vector = scam_vectorizer.transform([message])
        scam_prediction = scam_type_model.predict(scam_vector)[0]
        scam_type = str(scam_prediction)
    else:
        scam_type = "Not a Scam"

    # STEP 4: INDICATORS
    indicators = detect_indicators(message)

    # STEP 5: EXPLANATION
    if prediction == "spam":
        explanation = generate_explanation(
            scam_type,
            indicators
        )
    else:
        explanation = (
            "The message was classified as a normal message "
            "and does not contain enough characteristics to "
            "be identified as a scam."
        )

    # STEP 6: RECOMMENDATION
    recommendation = generate_recommendation(risk_level)

    # STEP 7: BUILD RESULT
    result = {
        "phone_number": str(phone_number),
        "country_code": str(country_code),
        "message_content": str(message),
        "scam_probability": int(scam_probability),
        "risk_level": str(risk_level),
        "scam_type": str(scam_type),
        "indicators": indicators,
        "explanation": str(explanation),
        "recommendation": str(recommendation)
    }

    # STEP 8: VALIDATE REQUIRED FIELDS AND TYPES
    for field, expected_type in required_fields.items():
        if field not in result:
            raise ValueError(f"Missing required field: {field}")

        if not isinstance(result[field], expected_type):
            raise TypeError(
                f"Invalid type for {field}. "
                f"Expected {expected_type.__name__}, "
                f"got {type(result[field]).__name__}"
            )

    if result:
        json_string = json.dump(result, indent=4, ensure_ascii=False)
        return json.loads(json_string) # return the AI output as a JSON object / pthon dict
    else:
        print("There was an error getting the result")


# ============================================================
# USER INPUT
# ============================================================

# print("\n")
# print("=" * 60)
# print("SCAM MESSAGE DETECTOR")
# print("=" * 60)

# phone_number = input("\nEnter sender phone number:\n> ")
# country_code = input("Enter country code (e.g. +65):\n> ")
# message = input("\nEnter message to analyse:\n> ")


# ============================================================
# ANALYSE
# ============================================================

# result = analyse_message(
#     message,
#     phone_number,
#     country_code
# )


# ============================================================
# JSON OUTPUT FOR LOGIC MANAGER
# ============================================================

# json_output = json.dumps(
#     result,
#     indent=4,
#     ensure_ascii=False
# )

# print(json_output)

# ============================================================
# DISPLAY RESULTS (ORIGINAL TERMINAL OUTPUT)
# ============================================================

# print("\n")
# print("=" * 60)
# print("SCAM DETECTION RESULT")
# print("=" * 60)

# print("\nMessage Input:")
# print(result["message_content"])

# print("\nScam Probability:")
# print(f'{result["scam_probability"]}%')

# print("\nRisk Level:")
# print(result["risk_level"])

# print("\nType of Scam:")
# print(result["scam_type"])

# print("\nWhat were the indicators of scam:")

# for indicator in result["indicators"]:
#     print(f"- {indicator}")

# print("\nExplanation of Indicators:")
# print(result["explanation"])

# print("\nRecommendation:")
# print(result["recommendation"])

# print("\n" + "=" * 60)