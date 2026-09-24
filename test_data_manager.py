from data_manager import load_records

scam_records = load_records()

print("Number of records:", len(scam_records))
print("First record:", scam_records[0])

for record in scam_records:
    print("\n========================================")
    print(f"          SCAM INCIDENT RECORD {record['message_id']} ")
    print("========================================")
    print(f"Timestamp        : {record['time_stamp']}")
    print(f"Phone Number     : {record['phone_number']}")
    print(f"Country Code     : {record['country_code']}")
    print(f"Risk Level       : {record['risk_level']}")
    print(f"Scam Probability : {record['scam_probability (%)']}%")
    print(f"Scam Type        : {record['scam_type']}")
    print(f"Message          : {record['message_content']}")
    print(f"Indicators       : {', '.join(record['indicators'])}")
    print(f"Explanation      : {record['explanation']}")
    print(f"Recommendation   : {record['recommendation']}")