#Read and write json format data
#Test
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



