import os, json
from models.record import Record
from datetime import datetime
from google import genai
from interfaces.ai_analyzer import AiAnalyzer

class GeminiAiAnalyzer(AiAnalyzer):
    def __init__(self, model="gemini-3.6-flash"):        
        self._client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) # get the API key
        self._model = model
    
    # Get response from Gemini API model
    def get_ai_output(self, prompt_to_ai):
        response = self._client.models.generate_content(
            model = self._model,
            contents = prompt_to_ai
        )
        return response.text
    
    # check if Gemini API is ready for use. Called once in AiManager.get_analyzer() to determine which AI Analyzer to use
    def check_api_status(self):
        print("Checking API Status. Please wait...\n")
        try:
            self.get_ai_output("Reply with the phrase: API IS OK.")
            return True
        except Exception as error:
            self.log_error(error) 
            return False

    # Retry function to get Gemini API output
    def get_ai_output_retry(self, prompt_to_ai):
        print(f"Retrying connection to Google {self._model} API once...")
        try:
            return self.get_ai_output(prompt_to_ai)
        except Exception as error:
            print("The API is still unavailable.")
            self.log_error(error)
            return False

    # grab only the JSON object in the AI output if there are strings before and after it
    def extract_json_object(self, text):
        start = text.find("{")
        end = text.rfind("}")    
        if start != -1 and end != -1: 
            json_string = text[start:end + 1]       
            json_object = json.loads(json_string)
            return json_object # return the JSON string as a JSON object
        
    # log any API failiures in a log file
    def log_error(self, error):
        with open("error.log", "a") as logfile:
            logfile.write(
                f"{datetime.now()} - API Error: {error}\n"
            )        

    # prompt containing user's message and phone number input
    def build_prompt(self, message, phone_number):
        prompt = f"""
        You are an AI Scam Risk Investigation Assistant.
        Analyse the following message and determine if it is potentially a scam.
        
        Message:
        {message}
        
        Source:
        {phone_number}
        
        Return a JSON object with the following fields:
        - scam_probability
        - risk_level
        - scam_type
        - indicators
        - explanation
        - recommendation
        
        Rules:
        - Messages can either be scam messages or legitimate messages.
        - Do not assume a message is a scam unless there are clear scam indicators.
        - The absence of scam indicators is evidence that a message is legitimate.
        - Ordinary greetings, personal conversations, social messages, appointment reminders, work discussions, family messages, scheduling messages, and casual communication should normally be classified as LOW risk.
        
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
            - Not Scam
        - Common scam message indicators include:
            - Urgency or pressure tactics
            - Threats or consequences
            - Requests for money
            - Requests for personal information
            - Requests for passwords, OTPs, or account verification
            - Suspicious links
            - Unexpected prizes or winnings
            - Impersonation of banks, government agencies, delivery companies, employers, or known organizations        
            
        - indicators must be a list of detected scam indicators from the analysed message. If no scam indicators are detected, indicators may be an empty list.
        - explanation, a string value, must explain why the message may be suspicious or why the message appears legitimate.
        - recommendation, a string value, must provide advice appropriate to the analysis result.
        
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
        return prompt
    
    def analyze_message(self, message, phone_number):
        prompt = self.build_prompt(message, phone_number)        
        print(f"Message analysis in progress using Google Gemini {self._model}. This may take a few seconds... \n")     

        try:
            response = self.get_ai_output(prompt)
        except Exception as error:
            print("The API is unavailable. Retrying once...")
            self.log_error(error)
            response = self.get_ai_output_retry(prompt) # retry once if the 2nd API call fails
            
        if response is False:
            return False # return to IO manager, prompt user if they want to use our custom AI bot or return to main menu
        
        # Check the AI Model API output. If response is a JSON string, convert it to JSON object. Else, call fallback function
        try:
            ai_output = json.loads(response)
        except json.JSONDecodeError as error:
            self.log_error(error)
            ai_output = self.extract_json_object(response)
        
        record = Record( # create a new Record object to store the AI output
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # format timestamp as YYYY-MM-DD HH:MM:SS
            phone_number = ai_output["phone_number"],
            country_code = ai_output["country_code"],
            message = ai_output["message_content"],
            scam_probability = ai_output["scam_probability"],
            risk_level = ai_output["risk_level"],
            scam_type = ai_output["scam_type"],
            indicators = ai_output["indicators"],
            explanation = ai_output["explanation"],
            recommendation = ai_output["recommendation"]        
        ) 
        print(record)
        return record
