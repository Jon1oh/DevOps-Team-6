from gemini_analyzer import GeminiAIAnalyzer
from dotenv import load_dotenv
import logging

load_dotenv()
logging.getLogger().setLevel(logging.ERROR) # hide warning messages from the Gemini SDK which uses Python's logging module

class AIManager:
    def get_analyzer(self):
        gemini_analyzer = GeminiAIAnalyzer()
        api_status = gemini_analyzer.check_api_status()
        
        if api_status is True:
            return gemini_analyzer
        else:
            pass # return FallbackAnalyzer object
            