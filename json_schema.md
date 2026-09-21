# Scam Record Schema
# The JSON format to store the user's scam message records in

```json
{
    "message_id": 1,
    "time_stamp": "2026-09-07 15:30:00",
    "phone_number": "",
    "message_content": "", # the actual message

    "scam_probability (%)": 0, # in percentage

    "risk_level": "Low", # High, Medium, or Low

    "scam_type": "", # Impersonation scam, Loan Scam, Job Scam, etc.

    "indicators": [],

    "explanation": "",

    "recommendation": ""
}
```