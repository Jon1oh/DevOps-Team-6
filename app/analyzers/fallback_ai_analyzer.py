import joblib, re
from pathlib import Path
from app.interfaces.ai_analyzer import AiAnalyzer
from app.models.record import Record
from datetime import datetime

class FallbackAiAnalyzer(AiAnalyzer):
    def __init__(self):
        # Load the trained machine learning model
        ROOT_DIR = Path(__file__).resolve().parent.parent.parent
        model_file = ROOT_DIR / "data" / "scam_detection_model.pkl"

        print("Loading Fallback AI model...")
        model_data = joblib.load(model_file)
        self._spam_model = model_data["spam_model"]
        self._spam_vectorizer = model_data["spam_vectorizer"]
        self._scam_type_model = model_data["scam_type_model"]
        self._scam_vectorizer = model_data["scam_vectorizer"]
        print("Fallback AI model loaded successfully.")
    
    # Detect suspicious indicators in a message
    def detect_indicators(self, message):
        indicators = []
        message_lower = message.lower()

        prize_words = [
            "won", "winner", "prize", "reward",
            "congratulations", "cash prize",
            "lucky draw", "claim"
        ]

        if any(word in message_lower for word in prize_words):
            indicators.append("Unexpected prize claim")

        if re.search(r"https?://", message_lower):
            indicators.append("Suspicious link")

        if re.search(r"\$\s?\d{1,3}(?:,\d{3})+", message):
            indicators.append("Large financial reward")

        suspicious_patterns = [
            r"congratulat0ns",
            r"cl@im",
            r"w1n",
            r"fr33",
            r"pr1ze",
            r"acc0unt"
        ]

        if any(
            re.search(pattern, message_lower)
            for pattern in suspicious_patterns
        ):
            indicators.append("Spelling mistakes")

        urgency_words = [
            "urgent", "immediately", "act now",
            "last chance", "within 24 hours"
        ]

        if any(word in message_lower for word in urgency_words):
            indicators.append("Urgent or threatening language")

        verification_words = [
            "verify your account",
            "verify your identity",
            "account suspended",
            "account locked"
        ]

        if any(word in message_lower for word in verification_words):
            indicators.append("Requests account verification")

        personal_information_words = [
            "password", "otp", "one-time password",
            "credit card", "card number",
            "nric", "personal information"
        ]

        if any(
            word in message_lower
            for word in personal_information_words
        ):
            indicators.append("Requests sensitive personal information")

        payment_words = [
            "transfer money", "send money",
            "bank transfer", "payment",
            "pay now", "deposit"
        ]

        if any(word in message_lower for word in payment_words):
            indicators.append("Requests payment or money transfer")

        return indicators

    # Determine risk level
    def get_risk_level(self, scam_probability):
        if scam_probability >= 80:
            return "HIGH"
        elif scam_probability >= 50:
            return "MEDIUM"
        return "LOW"

    # Generate explanation based on scam type
    def generate_explanation(self, scam_type, indicators):
        if scam_type == "Prize Scam":
            if (
                "Unexpected prize claim" in indicators
                and "Large financial reward" in indicators
            ):
                return (
                    "The message claims that the recipient has won "
                    "a large prize without any prior participation. "
                    "It also contains suspicious characteristics "
                    "commonly associated with prize scams."
                )

            return (
                "The message claims that the recipient has won "
                "a prize or reward and contains characteristics "
                "commonly associated with prize scams."
            )

        explanations = {

            "Banking Scam": (
                "The message contains banking-related language and "
                "may attempt to make the recipient verify an account, "
                "provide sensitive information, or take immediate action."
            ),

            "Phishing Scam": (
                "The message appears to be attempting to obtain "
                "sensitive information by directing the recipient "
                "to verify an account or follow a suspicious link."
            ),

            "Investment Scam": (
                "The message promotes a financial opportunity or "
                "investment and may attempt to persuade the recipient "
                "to provide money or personal information."
            ),

            "Job Scam": (
                "The message appears to offer a job or income "
                "opportunity and may contain suspicious requests "
                "for payment or personal information."
            ),

            "Loan Scam": (
                "The message appears to promote a loan or financial "
                "service and may request personal information, "
                "payments, or other sensitive details."
            )
        }

        return explanations.get(
            scam_type,
            "The message contains characteristics commonly "
            "associated with scam messages. The detected indicators "
            "suggest that the recipient should exercise caution."
        )

    # Generate recommendation based on risk level
    def generate_recommendation(self, risk_level):
        recommendations = {

            "HIGH": (
                "Do not click the link or provide personal information. "
                "Do not transfer money. Verify the message through the "
                "organisation's official website and report the "
                "message as suspicious."
            ),

            "MEDIUM": (
                "Be cautious with this message. Do not click suspicious "
                "links or provide personal information until the sender "
                "has been verified through an official source."
            ),

            "LOW": (
                "The message does not appear highly suspicious based "
                "on the current model prediction. However, remain "
                "cautious and verify unexpected requests before "
                "taking action."
            )
        }

        return recommendations[risk_level]

    # Main message analysis function
    def analyze_message(self, record: Record):
        if not isinstance(record.message, str):
            raise TypeError("Message must be a string.")

        # Convert message into numerical features
        message_vector = self._spam_vectorizer.transform([record.message])

        # Predict whether the message is spam
        prediction = self._spam_model.predict(message_vector)[0]

        # Obtain prediction probabilities
        probabilities = self._spam_model.predict_proba(message_vector)[0]

        class_probabilities = dict(
            zip(self._spam_model.classes_, probabilities)
        )

        # Extract spam probability
        spam_probability = next(
            (
                probability
                for label, probability in class_probabilities.items()
                if str(label).lower() == "spam"
            ),
            0
        )

        scam_probability = round(spam_probability * 100)

        is_spam = str(prediction).lower() == "spam"

        # Predict scam type if classified as spam
        if is_spam:

            scam_vector = self._scam_vectorizer.transform([record.message])

            scam_prediction = self._scam_type_model.predict(
                scam_vector
            )[0]

            scam_type = str(scam_prediction)

        else:
            scam_type = "Not a Scam"

        # Determine risk level
        risk_level = self.get_risk_level(scam_probability)

        # Detect suspicious indicators
        indicators = self.detect_indicators(record.message)

        # Generate explanation
        if is_spam:

            explanation = self.generate_explanation(
                scam_type,
                indicators
            )

        else:

            explanation = (
                "The message was classified as a normal message "
                "and does not contain enough characteristics to "
                "be identified as a scam."
            )

        # Generate recommendation
        recommendation = self.generate_recommendation(risk_level)

        # Populate Record object containing analysis results
        record.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # format timestamp as YYYY-MM-DD HH:MM:SS
        record.phone_number = str(record.phone_number)
        record.country_code=str(record.country_code)
        record.message=str(record.message)
        record.scam_probability=int(scam_probability)
        record.risk_level=risk_level
        record.scam_type=scam_type
        record.indicators=indicators
        record.explanation=explanation
        record.recommendation=recommendation
        
        return record
