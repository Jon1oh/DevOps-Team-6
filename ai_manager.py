from dotenv import load_dotenv
from google import genai
from datetime import datetime
import os, json, logging

load_dotenv()
logging.getLogger().setLevel(logging.ERROR) # hide warning messages from the Gemini SDK which uses Python's logging module
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) # get the API key
ai_model = "3.6-flash"
    

# function to get response from AI model, based on the prompt argument parsed
def get_ai_output(prompt_to_ai):
    response = client.models.generate_content(
        model=f"gemini-{ai_model}",
        contents=prompt_to_ai
    )
    return response.text


def get_ai_output_retry(prompt_to_ai):
    print(f"Retrying connection to Google Gemini {ai_model} API once...")
    try:
        return get_ai_output(prompt_to_ai)
    except Exception as error:
        print("The API is still unavailable.")
        log_error(error)
        return error


# grab only the JSON object in the AI output if there are strings before and after it
def extract_json_object(text):
    start = text.find("{")
    end = text.rfind("}")    
    if start != -1 and end != -1: 
        json_string = text[start:end + 1]       
        json_object = json.loads(json_string)
        return json_object # return the JSON string as a JSON object


# log any API failiures in a log file
def log_error(error):
    with open("error.log", "a") as logfile:
        logfile.write(
            f"{datetime.now()} - API Error: {error}\n"
        )
        
        
# check if the API is available to use or down due to high demand etc.
def check_api_status():
    print("Checking API Status. Please wait...\n")
    try:
        get_ai_output("Reply with the phrase: API IS OK.")
        return True
    except Exception as e:
        return e


def build_prompt(message, source):
    # the prompt to send to the AI model
    prompt = f"""
    You are an AI Scam Risk Investigation Assistant.
    Analyse the following message and determine if it is potentially a scam.
    
    Message:
    {message}
    
    Source:
    {source}
    
    Return a JSON object with the following fields:
    - scam_probability
    - risk_level
    - scam_type
    - indicators
    - explanation
    - recommendation
    
    Rules:
    - scam_probability must be an integer from 0 to 100.
    - risk_level, a string value, must be "HIGH" if scam_probability >= 80 and "MEDIUM" if scam_probability >= 50. Else, must be "LOW".
    - scam_type, a string value, must be one of the following:
        - Impersonation Scam
        - Banking Scam
        - Fake Subscription Scam
        - Fake Website Scam
        - Job Scam
        - Parcel Delivery Scam
        - Unexpected Prize Money Scam
        - Government Scam
        - Other Scam
    - indicators must be a list of detected scam indicators from the analysed message.
    - explanation, a string value, must explain why the message may be suspicious.
    - recommendation, a string value, must provide advice to the user on follow up actions based on the severity and type of scam message.
    
    Output restrictions:
    - Return only a JSON object in this format:
    {{
        "phone_number": "",
        "country_code": "",
        "message_content": "",
        "scam_probability": 0, 
        "risk_level": "",
        "scam_type": "",
        "indicators": [],
        "explanation": "",
        "recommendation": ""    
    }}
    - Do not include markdown, code blocks, or any text outside the JSON object.
    """
    
    # * message_id field will be added when writing to database.
    return prompt    
    

# check if message is a scam or not
def analyse_message(message_content, source_content):
    prompt = build_prompt(message_content, source_content)
    # prompt = "Return the phrase: My prompt for the AI." # * For simple testing purposes
    
    api_status = check_api_status() # Check API status before sending prompt to AI model. This is the 1st API call.
    
    if api_status is True:
        # print("API status is OK.")
        print(f"Message analysis in progress using Google Gemini {ai_model}. This may take a few seconds... \n")     
        
        # Use a try/except block since the 1st API call with check_api_status() doesn't guarantee a successful 2nd API call with get_ai_output()
        try:
            response = get_ai_output(prompt) # make 2nd API call to model to get AI output
        except Exception as error: 
            print(f"{error.message}\n")
            log_error(error)
            response = get_ai_output_retry(prompt) # retry API connection once
        
    else:
        # print("API status is not OK.")
        print(f"{api_status.message}\n") # api_status is a ServerError object when api is unavailable
        log_error(api_status)
        response = get_ai_output_retry(prompt)

    # Check the AI Model API output
    # if response is a JSON string, convert it to JSON object. Else, call fallback function
    if isinstance(response, str):
        try:
            ai_output = json.loads(response)
        except json.JSONDecodeError as error:
            log_error(error)
            ai_output = extract_json_object(response)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # format timestamp as YYYY-MM-DD HH:MM:SS
        ai_output = {"timestamp": timestamp, **ai_output} # insert timestamp at the front of the JSON object        
        print(ai_output)
        return ai_output
    else:
        # print(f"AI output is {type(response)}")
        return False
        # TODO: go back to IO manager, prompt user if they want to use our custom AI bot or return to main menu
        # TODO: Call fallback funtion (i.e. prompt user if they want to use our own bot        
    
    
test_message_content = """
URGENT: Your DBS account has been suspended due to suspicious activity.

To avoid permanent suspension, verify your account immediately at:

https://dbs-secure-verify.com

Failure to verify within 24 hours may result in account restrictions.

DBS Security Team
"""

test_message_source = "+6591234567"