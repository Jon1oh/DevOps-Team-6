#Read and write json format data

import json

DATA_FILE = "scam_data.json"

def load_records():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            print("file found")
            return json.load(file)

    except FileNotFoundError:
        print("file not found")
        return []

    except json.JSONDecodeError:
        print("decode error")
        return []
    
def count_risk_levels(phone_number, json_database):
    risk_record = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for entry in json_database:
        if entry.get("phone_number") == phone_number:
            if entry.get("risk_level") in risk_record.keys():
                risk_record[entry.get("risk_level")] += 1
    return risk_record