class Record:
    def __init__(self, phone_number, country_code, message, scam_probability, risk_level, scam_type, indicators, explanation, recommendation):
        self.phone_number = phone_number
        self.country_code = country_code
        self.message = message
        self.scam_probability = scam_probability
        self.risk_level = risk_level
        self.scam_type = scam_type
        self.indicators = indicators
        self.explanation = explanation
        self.recommendation = recommendation
        
    # Phone Number
    @property
    def phone_number(self):
        return self._phone_number

    @phone_number.setter
    def phone_number(self, value):
        self._phone_number = value

    # Country Code
    @property
    def country_code(self):
        return self._country_code

    @country_code.setter
    def country_code(self, value):
        self._country_code = value

    # Message
    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    # Scam Probability
    @property
    def scam_probability(self):
        return self._scam_probability

    @scam_probability.setter
    def scam_probability(self, value):
        # if not 0 <= value <= 100:
        #     raise ValueError(
        #         "Scam probability must be between 0 and 100."
        #     )
        self._scam_probability = value

    # Risk Level
    @property
    def risk_level(self):
        return self._risk_level

    @risk_level.setter
    def risk_level(self, value):
        # if value not in ["LOW", "MEDIUM", "HIGH"]:
        #     raise ValueError(
        #         "Risk level must be LOW, MEDIUM or HIGH."
        #     )
        self._risk_level = value

    # Scam Type
    @property
    def scam_type(self):
        return self._scam_type

    @scam_type.setter
    def scam_type(self, value):
        self._scam_type = value

    # Indicators
    @property
    def indicators(self):
        return self._indicators

    @indicators.setter
    def indicators(self, value):
        self._indicators = value

    # Explanation
    @property
    def explanation(self):
        return self._explanation

    @explanation.setter
    def explanation(self, value):
        self._explanation = value

    # Recommendation
    @property
    def recommendation(self):
        return self._recommendation

    @recommendation.setter
    def recommendation(self, value):
        self._recommendation = value