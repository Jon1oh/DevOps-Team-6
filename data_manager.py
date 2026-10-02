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

def save_record(record):
    records = load_records()
    records.append(record)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4)

def historical_summary(records):
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