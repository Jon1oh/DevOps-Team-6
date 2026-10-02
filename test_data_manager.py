from data_manager import load_records
from data_manager import save_record
from data_manager import message_summary

scam_records = load_records()

# print("Number of records:", len(scam_records))
# print("First record:", scam_records[0])

#---    PRINT EVERY RECORD     ----

# for record in scam_records:
#     print("\n========================================")
#     print(f"          SCAM INCIDENT RECORD {record['message_id']} ")
#     print("========================================")
#     print(f"Time stamp       : {record['timestamp']}")
#     print(f"Phone Number     : {record['phone_number']}")
#     print(f"Country Code     : {record['country_code']}")
#     print(f"Risk Level       : {record['risk_level']}")
#     print(f"Scam Probability : {record['scam_probability']}%")
#     print(f"Scam Type        : {record['scam_type']}")
#     print(f"Message          : {record['message_content']}")
#     print(f"Indicators       : {', '.join(record['indicators'])}")
#     print(f"Explanation      : {record['explanation']}")
#     print(f"Recommendation   : {record['recommendation']}")

    #test comment


#---    ADD NEW RECORD AND CHECK IF IT UPDATED  ---

# new_record = {
#         "message_id": 6,
#         "timestamp": "2026-10-02 11:40:00",
#         "phone_number": "+6591234567",
#         "country_code": "+65",
#         "message_content": "Your account has been suspended. Please click this link to verify: http://acount_recovery.com",
#         "scam_probability": 90,
#         "risk_level": "HIGH",
#         "scam_type": "Bank Impersonation Scam",
#         "indicators": [
#             "Urgent language",
#             "Suspicious link",
#         ],
#         "explanation": "The message impersonates a bank and asks the recipient to verify their account",
#         "recommendation": "Do not click the link. Contact the bank through its official website."
# }

# save_record(new_record)

summary = message_summary(scam_records)

def print_message_summary(summary):
    print("\n==============================")
    print("      SCAM MESSAGE SUMMARY")
    print("==============================\n")
    print(f"Total messages: {summary['total_messages']}\n")
    print("Risk Level Breakdown")
    print("------------------------------")

    for risk_level, count in summary["risk_level_breakdown"].items():
        print(f"{risk_level}: {count}")

    print()
    print("Scam Category Breakdown")
    print("------------------------------")

    for scam_type, count in summary["scam_category_breakdown"].items():
        print(f"{scam_type}: {count}")

    print()
    print("Country of Origin Breakdown")
    print("------------------------------")

    for country_code, count in summary["origin_country_breakdown"].items():
        print(f"{country_code}: {count}")

    print()
    print("Most Common type of Scam")
    print("------------------------------")
    print(summary["most_common_scam"])

print_message_summary(summary)