#Read and write json format data

import json, os, phonenumbers, tempfile, io_manager as IOManagerFile
from phonenumbers import geocoder

DATA_FILE = "./data/scam_data.json"
REAL_DATA_FILE = DATA_FILE 

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

def parse_phone_number(phone_number: str) -> phonenumbers.PhoneNumber | None:
    """Parse a phone number in international format (e.g. "+6591234567").

    Returns None if it is not text or cannot be understood.
    """
    if not isinstance(phone_number, str):
        return None
    try:
        return phonenumbers.parse(phone_number, None)
    except phonenumbers.NumberParseException:
        return None


def get_country_code(phone_number: str) -> str:
    """Return the calling code of a phone number, e.g. "+6591234567" -> "+65".

    Uses the phonenumbers library, so every country code is recognised.
    Returns "Unknown" if the number cannot be understood.
    """
    parsed = parse_phone_number(phone_number)
    if parsed is None:
        return "Unknown"
    return f"+{parsed.country_code}"


def get_country_name(country_code: str) -> str:
    """Convert a calling code to its main country name, e.g. "+65" -> "Singapore".

    Some codes are shared by several countries (e.g. "+1" is the USA, Canada and
    others); this returns the main one. Returns "Unknown" if the code is not real.
    """
    if not isinstance(country_code, str) or not country_code.lstrip("+").isdigit():
        return "Unknown"
    region = phonenumbers.region_code_for_country_code(int(country_code.lstrip("+")))
    example = phonenumbers.example_number(region)
    if example is None:
        return "Unknown"
    return geocoder.country_name_for_number(example, "en") or "Unknown"


def get_country_name_for_number(phone_number: str) -> str:
    """Return the country a specific phone number is from, e.g. "+16135550123" -> "Canada".

    More precise than get_country_name() for shared codes like "+1".
    """
    parsed = parse_phone_number(phone_number)
    if parsed is None:
        return "Unknown"
    name = geocoder.country_name_for_number(parsed, "en")
    if name:
        return name
    return get_country_name(f"+{parsed.country_code}")


def get_country_label(country_code: str) -> str:
    """Return the code with its country name, e.g. "+65" -> "+65 (Singapore)"."""
    return f"{country_code} ({get_country_name(country_code)})"


def standardize_record(record: dict) -> dict:
    """Return a copy of `record` that follows the agreed schema.

    - fills in country_code from the phone number if it is missing
    - upper-cases risk_level ("High" -> "HIGH")
    - fills any still-missing field with a safe default
    """
    fixed = dict(record)

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


def get_next_message_id(records: list[dict]) -> int:
    """Return the next free message_id: highest existing id + 1, or 1 if there are none."""
    highest = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        message_id = record.get("message_id")
        if isinstance(message_id, int) and not isinstance(message_id, bool) and message_id > highest:
            highest = message_id
    return highest + 1


def save_record(record: dict) -> tuple[bool, str]:
    """Standardize, number, validate, then append one record to DATA_FILE.

    The record is always given the next free message_id, so ids never repeat.
    Returns (True, "") on success or (False, "reason") on failure.
    """
    records = load_records()
    record = standardize_record(record)
    record["message_id"] = get_next_message_id(records)

    is_valid, error = validate_record(record)
    if not is_valid:
        return False, error

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
    summary["most_common_scam_percentage"] =  get_most_common_scam_type(records)
    summary["most_common_origin"] = get_most_common_origin(records)

    # summary["most_common_scam"] = (
    #     summary["most_common_scam_percentage"][0]
    #     if summary["most_common_scam_percentage"] is not None
    #     else "Unknown"
    # )
    most_common_scam = get_most_common_scam_type(records)

    summary["most_common_scam_percentage"] = most_common_scam
    summary["most_common_scam"] = (
        most_common_scam[0] if most_common_scam is not None else "Unknown"
    )

    # Country names for display, e.g. {"+65": "+65 (Singapore)"}
    summary["origin_country_labels"] = {}
    for country_code in summary["origin_country_breakdown"]:
        summary["origin_country_labels"][country_code] = get_country_label(country_code)
    return summary


# =====================================================================
# test functions
# =====================================================================

def use_temp_file(contents: str | None) -> str:
    global DATA_FILE
    """Point data_manager at a fresh temporary file (optionally with contents)."""
    folder = tempfile.mkdtemp()
    path = os.path.join(folder, "scam_data.json")
    if contents is not None:
        with open(path, "w", encoding="utf-8") as file:
            file.write(contents)
    DATA_FILE = path
    return path


def make_valid_record() -> dict:
    return {
        "message_id": 1,
        "timestamp": "2026-10-02 11:40:00",
        "phone_number": "+6591234567",
        "country_code": "+65",
        "message_content": "Your account is suspended. Click http://bad.link",
        "scam_probability": 90,
        "risk_level": "HIGH",
        "scam_type": "Bank Impersonation Scam",
        "indicators": ["Urgent language", "Suspicious link"],
        "explanation": "Impersonates a bank.",
        "recommendation": "Do not click the link.",
    }


SAMPLE_RECORDS = [
    {"country_code": "+65", "scam_type": "Phishing"},
    {"country_code": "+65", "scam_type": "Phishing"},
    {"country_code": "+60", "scam_type": "Delivery"},
    {"country_code": "+65", "scam_type": "Job scam"},
]


# ---------- percentage / most-common ----------

def test_percentage_basic() -> None:
    assert calculate_percentage({"A": 3, "B": 1}) == {"A": 75.0, "B": 25.0}


def test_percentage_empty() -> None:
    assert calculate_percentage({}) == {}


def test_percentage_rounding() -> None:
    assert calculate_percentage({"A": 1, "B": 2}) == {"A": 33.33, "B": 66.67}


def test_most_common_origin() -> None:
    assert get_most_common_origin(SAMPLE_RECORDS) == ("+65", 75.0)
    assert get_most_common_origin([]) is None


def test_most_common_scam_type() -> None:
    assert get_most_common_scam_type(SAMPLE_RECORDS) == ("Phishing", 50.0)
    assert get_most_common_scam_type([]) is None


def test_tie_is_alphabetical() -> None:
    tie = [{"scam_type": "Phishing"}, {"scam_type": "Delivery"}]
    assert get_most_common_scam_type(tie) == ("Delivery", 50.0)


# ---------- schema ----------

def test_valid_record_passes() -> None:
    assert validate_record(make_valid_record()) == (True, "")


def test_missing_field_fails() -> None:
    record = make_valid_record()
    del record["scam_type"]
    assert validate_record(record) == (False, "Missing field: scam_type")


def test_wrong_type_fails() -> None:
    record = make_valid_record()
    record["scam_probability"] = "90"
    assert validate_record(record)[0] is False


def test_bad_risk_level_fails() -> None:
    record = make_valid_record()
    record["risk_level"] = "VERY HIGH"
    assert validate_record(record)[0] is False


def test_probability_out_of_range_fails() -> None:
    record = make_valid_record()
    record["scam_probability"] = 150
    assert validate_record(record)[0] is False


def test_standardize_uppercases_risk_level() -> None:
    fixed = standardize_record({"risk_level": "High", "phone_number": "+6591234567"})
    assert fixed["risk_level"] == "HIGH"
    assert fixed["country_code"] == "+65"


def test_country_code_from_phone() -> None:
    assert get_country_code("+6591234567") == "+65"
    assert get_country_code("+2348012345678") == "+234"
    assert get_country_code("+819012345678") == "+81"      # Japan - not in the old fixed list
    assert get_country_code("91234567") == "Unknown"       # no + country code
    assert get_country_code("hello") == "Unknown"


def test_country_name_from_code() -> None:
    assert get_country_name("+65") == "Singapore"
    assert get_country_name("+81") == "Japan"
    assert get_country_name("+999") == "Unknown"
    assert get_country_name("Unknown") == "Unknown"


def test_country_name_for_number() -> None:
    assert get_country_name_for_number("+14155550123") == "United States"
    assert get_country_name_for_number("+16135550123") == "Canada"   # same +1 code
    assert get_country_name_for_number("abc") == "Unknown"


# ---------- corrupt JSON handling ----------

def test_missing_file_returns_empty() -> None:
    use_temp_file(None)
    assert load_records() == []


def test_corrupt_file_is_backed_up() -> None:
    path = use_temp_file("{ this is not valid json")
    records, status = load_records_with_status()
    assert records == []
    assert "corrupt" in status
    assert os.path.exists(path.replace(".json", ".corrupt.json"))


def test_non_list_file_is_handled() -> None:
    use_temp_file('{"not": "a list"}')
    assert load_records() == []


def test_corrupt_entries_are_skipped() -> None:
    use_temp_file(json.dumps([make_valid_record(), "garbage", 42]))
    records, status = load_records_with_status()
    assert len(records) == 1
    assert "Skipped 2" in status


def test_summary_survives_records_missing_keys() -> None:
    use_temp_file(json.dumps([{"phone_number": "+6591234567"}]))
    records = load_records()
    summary = summary_with_percentages(records)
    assert summary["total_messages"] == 1


def test_save_then_load() -> None:
    use_temp_file(None)
    assert save_record(make_valid_record()) == (True, "")
    assert len(load_records()) == 1


def test_invalid_record_is_not_saved() -> None:
    use_temp_file(None)
    bad = make_valid_record()
    bad["message_content"] = ""
    ok, _error = save_record(bad)
    assert ok is False
    assert load_records() == []


# ---------- message_id ----------

def test_next_message_id() -> None:
    assert get_next_message_id([]) == 1
    assert get_next_message_id([{"message_id": 3}, {"message_id": 7}]) == 8
    assert get_next_message_id([{"message_id": "x"}, "corrupt"]) == 1


def test_save_assigns_message_ids_in_order() -> None:
    use_temp_file(None)
    save_record(make_valid_record())
    save_record(make_valid_record())     # same input id (1) on purpose
    ids = [record["message_id"] for record in load_records()]
    assert ids == [1, 2]                     # no duplicates


# ---------- country name ----------

def test_country_label() -> None:
    assert get_country_label("+65") == "+65 (Singapore)"
    assert get_country_label("+999") == "+999 (Unknown)"


def test_summary_has_country_labels() -> None:
    records = [{"risk_level": "HIGH", "scam_type": "Phishing", "country_code": "+44"}]
    summary = summary_with_percentages(records)
    assert summary["origin_country_labels"] == {"+44": "+44 (United Kingdom)"}


# ---------- count_risk_levels ----------

def test_count_risk_levels_for_one_number() -> None:
    records = [
        {"phone_number": "+6591234567", "risk_level": "HIGH"},
        {"phone_number": "+6591234567", "risk_level": "LOW"},
        {"phone_number": "+6500000000", "risk_level": "HIGH"},
    ]
    use_temp_file(json.dumps(records))
    assert count_risk_levels("+6591234567") == {"HIGH": 1, "MEDIUM": 0, "LOW": 1}
    assert count_risk_levels("+6599999999") == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}


# functions to run the tests 

def run_all_tests() -> int:
    global DATA_FILE
    """Run every test_ function and print PASS/FAIL. Returns the number of failures."""
    all_tests = [value for name, value in list(globals().items())
                 if name.startswith("test_") and callable(value)]
    failed = 0
    try:
        for test in all_tests:
            try:
                test()
                print(f"PASS  {test.__name__}")
            except AssertionError:
                print(f"FAIL  {test.__name__}")
                failed += 1
    finally:
        DATA_FILE = REAL_DATA_FILE
    print(f"\n{len(all_tests) - failed}/{len(all_tests)} tests passed")
    return failed


def run_demo() -> None:
    global DATA_FILE
    """Load the real scam_data.json and print its summary (read-only)."""
    DATA_FILE = REAL_DATA_FILE
    scam_records = load_records()
    print(scam_records)
    # print_all_records(scam_records)    # uncomment to see every record
    IOManagerFile.print_message_summary(summary_with_percentages(scam_records))


if __name__ == "__main__":
    run_all_tests()
    run_demo()