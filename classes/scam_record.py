"""ScamRecord: for one analysed SMS message."""

import phonenumbers

class ScamRecord:
    """One analysed SMS message with its 11 fields.
 
    Every field is stored in a private attribute (e.g. self._risk_level) and
    accessed through a property. The property setters check the value, so a
    ScamRecord object can never hold invalid data (encapsulation).
    """

    VALID_RISK_LEVELS = ("HIGH", "MEDIUM", "LOW")

    # Values used when a field is missing from a saved dictionary.
    FIELD_DEFAULTS = {
        "message_id": 0,
        "timestamp": "Unknown",
        "phone_number": "Unknown",
        "country_code": "Unknown",
        "message_content": "",
        "scam_probability": 0,
        "risk_level": "Unknown",
        "scam_type": "Unknown",
        "indicators": [],
        "explanation": "",
        "recommendation": "",
    }

    def __init__(
        self,
        message_id: int,
        timestamp: str,
        phone_number: str,
        country_code: str,
        message_content: str,
        scam_probability: int | float,
        risk_level: str,
        scam_type: str,
        indicators: list,
        explanation: str,
        recommendation: str,
    ) -> None:
        # Each line below calls a property setter, so every value is checked.
        self.message_id = message_id
        self.timestamp = timestamp
        self.phone_number = phone_number
        self.country_code = country_code
        self.message_content = message_content
        self.scam_probability = scam_probability
        self.risk_level = risk_level
        self.scam_type = scam_type
        self.indicators = indicators
        self.explanation = explanation
        self.recommendation = recommendation

        
    # Private helpers used by the setters

    @staticmethod
    def _check_text(value: object, field: str) -> str:
        """Return value if it is a string, otherwise raise ValueError."""
        if not isinstance(value, str):
            raise ValueError(f"Wrong type for field: {field}")
        return value  
    
    # ------------------------------------------------------------------
    # Properties (getter + validating setter for each field)     
    # ------------------------------------------------------------------
    
    @property
    def message_id(self) -> int:
        return self._message_id    

    @message_id.setter
    def message_id(self, value: int) -> None:
        # bool is a kind of int in Python (True == 1), so reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("message_id must be a whole number of 0 or more.")
        self._message_id = value

    @property
    def timestamp(self) -> str:
        return self._timestamp
 
    @timestamp.setter
    def timestamp(self, value: str) -> None:
        self._timestamp = self._check_text(value, "timestamp")
 
    @property
    def phone_number(self) -> str:
        return self._phone_number

    @phone_number.setter
    def phone_number(self, value: str) -> None:
        self._phone_number = self._check_text(value, "phone_number")

    @property
    def country_code(self) -> str:
        return self._country_code

    @country_code.setter
    def country_code(self, value: str) -> None:
        self._country_code = self._check_text(value, "country_code")
 
    @property
    def message_content(self) -> str:
        return self._message_content

    @message_content.setter
    def message_content(self, value: str) -> None:
        value = self._check_text(value, "message_content")
        if value.strip() == "":
            raise ValueError("message_content cannot be empty.")
        self._message_content = value
 
    @property
    def scam_probability(self) -> int | float:
        return self._scam_probability

    @scam_probability.setter
    def scam_probability(self, value: int | float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Wrong type for field: scam_probability")
        if not 0 <= value <= 100:
            raise ValueError("scam_probability must be between 0 and 100.")
        self._scam_probability = value
 
    @property
    def risk_level(self) -> str:
        return self._risk_level

    @risk_level.setter
    def risk_level(self, value: str) -> None:
        value = self._check_text(value, "risk_level").strip().upper()
        if value not in self.VALID_RISK_LEVELS:
            raise ValueError("risk_level must be HIGH, MEDIUM or LOW.")
        self._risk_level = value
 
    @property
    def scam_type(self) -> str:
        return self._scam_type
 
    @scam_type.setter
    def scam_type(self, value: str) -> None:
        self._scam_type = self._check_text(value, "scam_type")

    @property
    def indicators(self) -> list:
        # Return a copy, so code outside cannot change our list by accident.
        return list(self._indicators)
 
    @indicators.setter
    def indicators(self, value: list) -> None:
        if not isinstance(value, list):
            raise ValueError("Wrong type for field: indicators")
        self._indicators = list(value)
 
    @property
    def explanation(self) -> str:
        return self._explanation

    @explanation.setter
    def explanation(self, value: str) -> None:
        self._explanation = self._check_text(value, "explanation")
 
    @property
    def recommendation(self) -> str:
        return self._recommendation
 
    @recommendation.setter
    def recommendation(self, value: str) -> None:
        self._recommendation = self._check_text(value, "recommendation")

    # ------------------------------------------------------------------
    # Converting to and from dictionaries (for JSON storage)
    # ------------------------------------------------------------------
 
    @staticmethod
    def country_code_from_phone(phone_number: str) -> str:
        """Return the calling code of a number, e.g. "+6591234567" -> "+65"."""
        if not isinstance(phone_number, str):
            return "Unknown"
        try:
            parsed = phonenumbers.parse(phone_number, None)
        except phonenumbers.NumberParseException:
            return "Unknown"
        return f"+{parsed.country_code}"
 
    @classmethod
    def from_dict(cls, data: object) -> tuple["ScamRecord | None", str]:
        """Build a ScamRecord from a dictionary (e.g. one entry in the JSON file).
 
        Standardises the data first (same rules as Phase 1), then validates it.
        Returns (record, "") on success, or (None, "reason") if the data is invalid.
        """
        if not isinstance(data, dict):
            return None, "Record is not a dictionary."
 
        fixed = dict(data)  # work on a copy, never change the caller's dict
 
        if not fixed.get("country_code"):
            fixed["country_code"] = cls.country_code_from_phone(
                fixed.get("phone_number", "")
            )
 
        for key, default in cls.FIELD_DEFAULTS.items():
            if key not in fixed:
                fixed[key] = list(default) if isinstance(default, list) else default
 
        try:
            record = cls(
                message_id=fixed["message_id"],
                timestamp=fixed["timestamp"],
                phone_number=fixed["phone_number"],
                country_code=fixed["country_code"],
                message_content=fixed["message_content"],
                scam_probability=fixed["scam_probability"],
                risk_level=fixed["risk_level"],
                scam_type=fixed["scam_type"],
                indicators=fixed["indicators"],
                explanation=fixed["explanation"],
                recommendation=fixed["recommendation"],
            )
        except ValueError as error:
            return None, str(error)
 
        return record, ""
 
    def to_dict(self) -> dict:
        """Return this record as a plain dictionary, ready for json.dump()."""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "phone_number": self.phone_number,
            "country_code": self.country_code,
            "message_content": self.message_content,
            "scam_probability": self.scam_probability,
            "risk_level": self.risk_level,
            "scam_type": self.scam_type,
            "indicators": self.indicators,
            "explanation": self.explanation,
            "recommendation": self.recommendation,
        }