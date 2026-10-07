#Read and write json format data

import json
import os

DATA_FILE = "scam_data.json"


# =====================================================================
# Record schema (matches json_schema.md)
# =====================================================================

# Every saved record must have these keys, with these types
RECORD_SCHEMA: dict[str, type | tuple[type, ...]] = {
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

VALID_RISK_LEVELS = ("HIGH", "MEDIUM", "LOW")

# Old key names found in earlier records -> the agreed schema name
OLD_KEY_NAMES = {
    "time_stamp": "timestamp",
    "scam_probability (%)": "scam_probability",
}

# Default value used when a field is missing from an old/broken record
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

# Known calling codes -> country name (longest codes are checked first)
COUNTRY_CODES = {
    "+1": "USA/Canada", "+44": "United Kingdom", "+60": "Malaysia",
    "+61": "Australia", "+62": "Indonesia", "+63": "Philippines",
    "+65": "Singapore", "+66": "Thailand", "+84": "Vietnam",
    "+86": "China", "+91": "India", "+234": "Nigeria", "+852": "Hong Kong",
}


def get_country_code(phone_number: str) -> str:
    """Return the calling code at the start of a phone number, e.g. "+6591234567" -> "+65".

    Returns "Unknown" if the number does not start with a known code.
    """
    if not isinstance(phone_number, str):
        return "Unknown"
    number = phone_number.replace(" ", "")
    for code in sorted(COUNTRY_CODES, key=len, reverse=True):
        if number.startswith(code):
            return code
    return "Unknown"


def get_country_name(country_code: str) -> str:
    """Convert a calling code to a country name, e.g. "+65" -> "Singapore"."""
    return COUNTRY_CODES.get(country_code, "Unknown")


def standardize_record(record: dict) -> dict:
    """Return a copy of `record` that follows the agreed schema.

    - renames old keys (e.g. "time_stamp" -> "timestamp")
    - fills in country_code from the phone number if it is missing
    - upper-cases risk_level ("High" -> "HIGH")
    - fills any still-missing field with a safe default
    """
    fixed: dict = {}
    for key, value in record.items():
        fixed[OLD_KEY_NAMES.get(key, key)] = value

    if not fixed.get("country_code"):
        fixed["country_code"] = get_country_code(fixed.get("phone_number", ""))

    if isinstance(fixed.get("risk_level"), str):
        fixed["risk_level"] = fixed["risk_level"].strip().upper()

    for key, default in FIELD_DEFAULTS.items():
        if key not in fixed:
            fixed[key] = list(default) if isinstance(default, list) else default
    return fixed


def validate_record(record: dict) -> tuple[bool, str]:
    """Check a record against the schema before it is saved.

    Returns (True, "") if valid, otherwise (False, "reason it failed").
    """
    if not isinstance(record, dict):
        return False, "Record is not a dictionary."

    for key, expected_type in RECORD_SCHEMA.items():
        if key not in record:
            return False, f"Missing field: {key}"
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, expected_type):
            return False, f"Wrong type for field: {key}"

    if record["risk_level"] not in VALID_RISK_LEVELS:
        return False, "risk_level must be HIGH, MEDIUM or LOW."
    if not 0 <= record["scam_probability"] <= 100:
        return False, "scam_probability must be between 0 and 100."
    if record["message_content"].strip() == "":
        return False, "message_content cannot be empty."
    return True, ""


# =====================================================================
# Loading and saving (with corrupt-file handling)
# =====================================================================

def backup_corrupt_file() -> str:
    """Rename a corrupt DATA_FILE so its contents are not overwritten.

    Returns the backup file name, or "" if the rename failed.
    """
    backup_name = DATA_FILE.replace(".json", ".corrupt.json")
    try:
        os.replace(DATA_FILE, backup_name)
    except OSError:
        return ""
    return backup_name


def load_records_with_status() -> tuple[list[dict], str]:
    """Load records and also return a status message for io_manager to display.

    Status is "" when everything loaded normally.
    """
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return [], "No saved records yet - starting fresh."
    except (json.JSONDecodeError, UnicodeDecodeError):
        backup = backup_corrupt_file()
        return [], f"Data file was corrupt. Backed up to {backup} and started fresh."

    if not isinstance(data, list):
        backup = backup_corrupt_file()
        return [], f"Data file had the wrong format. Backed up to {backup} and started fresh."

    records: list[dict] = []
    skipped = 0
    for entry in data:
        if isinstance(entry, dict):
            records.append(standardize_record(entry))
        else:
            skipped += 1

    if skipped > 0:
        return records, f"Skipped {skipped} corrupt record(s)."
    return records, ""


def load_records() -> list[dict]:
    """Load all records from DATA_FILE. Never crashes; returns [] if the file is missing or corrupt."""
    records, _status = load_records_with_status()
    return records


def save_record(record: dict) -> tuple[bool, str]:
    """Standardize, validate, then append one record to DATA_FILE.

    Returns (True, "") on success or (False, "reason") on failure.
    """
    record = standardize_record(record)
    is_valid, error = validate_record(record)
    if not is_valid:
        return False, error

    records = load_records()
    records.append(record)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=4)
    except OSError:
        return False, "Could not write to the data file."
    return True, ""


# =====================================================================
# Teammate's query and summary functions (unchanged)
# =====================================================================

def count_risk_levels(phone_number):
    risk_record = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for entry in load_records():
        if entry.get("phone_number") == phone_number:
            if entry.get("risk_level") in risk_record.keys():
                risk_record[entry.get("risk_level")] += 1
    return risk_record

def message_summary(records):
    risk_level_breakdown = {}
    scam_category_breakdown = {}
    origin_country_breakdown = {}
    most_common_scam = None
    most_common_count = 0

    for record in records:
        risk_level = record["risk_level"]

        if risk_level in risk_level_breakdown:
            risk_level_breakdown[risk_level] += 1
        else:
            risk_level_breakdown[risk_level] = 1


        scam_type = record["scam_type"]

        if scam_type in scam_category_breakdown:
            scam_category_breakdown[scam_type] += 1
        else:
            scam_category_breakdown[scam_type] = 1


        country_code = record["country_code"]

        if country_code in origin_country_breakdown:
            origin_country_breakdown[country_code] += 1
        else:
            origin_country_breakdown[country_code] = 1


    for scam_type, count in scam_category_breakdown.items():
        if count > most_common_count:
            most_common_scam = scam_type
            most_common_count = count


    return {
        "total_messages": len(records),
        "risk_level_breakdown": risk_level_breakdown,
        "scam_category_breakdown": scam_category_breakdown,
        "origin_country_breakdown": origin_country_breakdown,
        "most_common_scam": most_common_scam
    }


# =====================================================================
# Kelvin's section: percentage and most-common functions
# =====================================================================

SCAM_TYPE_FIELD = "scam_type"
ORIGIN_FIELD = "country_code"


def count_field(records: list[dict], field: str) -> dict[str, int]:
    """Count how many records have each value of `field`.

    Missing, empty or non-string values are counted as "Unknown";
    non-dict (corrupt) entries are skipped.
    """
    counts: dict[str, int] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(field)
        if not isinstance(value, str) or value.strip() == "":
            value = "Unknown"
        else:
            value = value.strip()
        counts[value] = counts.get(value, 0) + 1
    return counts


def calculate_percentage(counts: dict[str, int]) -> dict[str, float]:
    """Convert counts into percentages of the total, rounded to 2 d.p."""
    total = sum(counts.values())
    if total == 0:
        return {}

    percentages: dict[str, float] = {}
    for name, count in counts.items():
        percentages[name] = round(count / total * 100, 2)
    return percentages


def get_top_entry(percentages: dict[str, float]) -> tuple[str, float] | None:
    """Return the (name, percentage) with the highest percentage.

    Ties are broken alphabetically so results are the same every run.
    """
    if not percentages:
        return None

    top_name = ""
    top_percent = -1.0
    for name in sorted(percentages):
        if percentages[name] > top_percent:
            top_name = name
            top_percent = percentages[name]
    return top_name, top_percent


def get_most_common_origin(records: list[dict]) -> tuple[str, float] | None:
    """Return the country code with the highest % of messages, e.g. ("+65", 62.5)."""
    return get_top_entry(calculate_percentage(count_field(records, ORIGIN_FIELD)))


def get_most_common_scam_type(records: list[dict]) -> tuple[str, float] | None:
    """Return the scam type with the highest % of messages, e.g. ("Phishing", 40.0)."""
    return get_top_entry(calculate_percentage(count_field(records, SCAM_TYPE_FIELD)))


def summary_with_percentages(records: list[dict]) -> dict:
    """Take message_summary() and add percentage breakdowns and most-common origin."""
    summary = message_summary(records)
    summary["risk_level_percentage"] = calculate_percentage(summary["risk_level_breakdown"])
    summary["scam_category_percentage"] = calculate_percentage(summary["scam_category_breakdown"])
    summary["origin_country_percentage"] = calculate_percentage(summary["origin_country_breakdown"])
    summary["most_common_scam_percentage"] = get_most_common_scam_type(records)
    summary["most_common_origin"] = get_most_common_origin(records)
    return summary