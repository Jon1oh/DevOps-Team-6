
import os, json
from google import genai
from interfaces.ai_analyzer import AIAnalyzer

class GeminiAIAnalyzer(AIAnalyzer):
    def __init__(self):
        self._client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) # get the API key
        self._ai_model = "3.6-flash"
    
    def get_ai_output(self, prompt_to_ai):
        response = self._client.models.generate_content(
            model=f"gemini-{self._ai_model}",
            contents=prompt_to_ai
        )
        return response.text
    
    
    def check_api_status(self):
        print("Checking API Status. Please wait...\n")
        try:
            self.get_ai_output("Reply with the phrase: API IS OK.")
            return True
        except Exception as e:
            return e

    def get_ai_output_retry(self, prompt_to_ai):
        print(f"Retrying connection to Google Gemini {self.ai_model} API once...")
        try:
            return self.get_ai_output(prompt_to_ai)
        except Exception as error:
            print("The API is still unavailable.")
            # log_error(error)
            return error

    # grab only the JSON object in the AI output if there are strings before and after it
    def extract_json_object(self, text):
        start = text.find("{")
        end = text.rfind("}")    
        if start != -1 and end != -1: 
            json_string = text[start:end + 1]       
            json_object = json.loads(json_string)
            return json_object # return the JSON string as a JSON object

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
    
    def analyze_message(self):
        pass