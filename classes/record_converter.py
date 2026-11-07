"""RecordConverter: turns Record objects into JSON dictionaries.

- record.py holds the data
- record_converter.py class holds the rules for storing that data e.g. the JSON key names (message_id, message_content, ...), 
standardising (defaults, upper-case risk level, country code from phone), validation (correct types, HIGH/MEDIUM/LOW, 0-100, message not empty).
"""

import phonenumbers

from record import Record


class RecordConverter:
    """Converts between Record objects and the dictionaries in scam_data.json.

    All methods are class methods: you call them on the class itself,
    e.g. RecordConverter.to_dict(record). The class keeps the storage schema
    in one place, so every storage class uses exactly the same rules.
    """

    VALID_RISK_LEVELS = ("HIGH", "MEDIUM", "LOW")

    # JSON key -> the type it must have (bool is rejected separately).
    SCHEMA: dict[str, type | tuple[type, ...]] = {
        "message_id": int,
        "timestamp": str,
        "phone_number": str,
        "country_code": str,
        "message_content": str,
        "scam_probability": (int, float),
        "risk_level": str,
        "scam_type": str,
        "indicators": list,
        "explanation": str,
        "recommendation": str,
    }

    # Value used when a key is missing from a saved dictionary.
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

    # ------------------------------------------------------------------
    # conver record to dictionary
    # ------------------------------------------------------------------

    @classmethod
    def to_dict(cls, record: Record) -> dict:
        """Return a Record as a dictionary with the JSON key names.

        Record calls the id `record_id` and the text `message`; the JSON file
        calls them `message_id` and `message_content`. All other names match.
        """
        return {
            "message_id": record.record_id,
            "timestamp": record.timestamp,
            "phone_number": record.phone_number,
            "country_code": record.country_code,
            "message_content": record.message,
            "scam_probability": record.scam_probability,
            "risk_level": record.risk_level,
            "scam_type": record.scam_type,
            "indicators": record.indicators,
            "explanation": record.explanation,
            "recommendation": record.recommendation,
        }

    # ------------------------------------------------------------------
    # convert dictionary to Record
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: object) -> tuple[Record | None, str]:
        """Standardise and validate a dictionary, then build a Record.

        Returns (record, "") if the data is valid, or (None, "reason") if not.
        The caller's dictionary is never changed.
        """
        if not isinstance(data, dict):
            return None, "Record is not a dictionary."

        fixed = cls.standardize(data)
        is_valid, error = cls.validate(fixed)
        if not is_valid:
            return None, error

        record = Record(
            record_id=fixed["message_id"],
            timestamp=fixed["timestamp"],
            phone_number=fixed["phone_number"],
            country_code=fixed["country_code"],
            message=fixed["message_content"],
            scam_probability=fixed["scam_probability"],
            risk_level=fixed["risk_level"],
            scam_type=fixed["scam_type"],
            indicators=list(fixed["indicators"]),
            explanation=fixed["explanation"],
            recommendation=fixed["recommendation"],
        )
        return record, ""

    # ------------------------------------------------------------------
    # Checking a Record that was built somewhere else
    # ------------------------------------------------------------------

    @classmethod
    def check_record(cls, record: object) -> tuple[bool, str]:
        """Check a Record object before it is saved. Returns (ok, reason)."""
        if not isinstance(record, Record):
            return False, "Only Record objects can be saved."
        return cls.validate(cls.to_dict(record))

    # ------------------------------------------------------------------
    # standardize_record and validate_record
    # ------------------------------------------------------------------

    @classmethod
    def standardize(cls, data: dict) -> dict:
        """Return a cleaned-up COPY of `data`.

        - fills in country_code from the phone number if it is missing
        - upper-cases risk_level ("High" -> "HIGH")
        - fills any still-missing key with a safe default
        """
        fixed = dict(data)

        if not fixed.get("country_code"):
            fixed["country_code"] = cls.country_code_from_phone(
                fixed.get("phone_number", "")
            )

        if isinstance(fixed.get("risk_level"), str):
            fixed["risk_level"] = fixed["risk_level"].strip().upper()

        for key, default in cls.FIELD_DEFAULTS.items():
            if key not in fixed:
                fixed[key] = list(default) if isinstance(default, list) else default
        return fixed

    @classmethod
    def validate(cls, data: dict) -> tuple[bool, str]:
        """Check a dictionary against the schema. Returns (True, "") or (False, reason)."""
        for key, expected_type in cls.SCHEMA.items():
            if key not in data:
                return False, f"Missing field: {key}"
            value = data[key]
            # bool is a kind of int in Python (True == 1), so reject it explicitly.
            if isinstance(value, bool) or not isinstance(value, expected_type):
                return False, f"Wrong type for field: {key}"

        if data["message_id"] < 0:
            return False, "message_id cannot be negative."
        if data["risk_level"] not in cls.VALID_RISK_LEVELS:
            return False, "risk_level must be HIGH, MEDIUM or LOW."
        if not 0 <= data["scam_probability"] <= 100:
            return False, "scam_probability must be between 0 and 100."
        if data["message_content"].strip() == "":
            return False, "message_content cannot be empty."
        return True, ""

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