from gemini_analyzer import GeminiAiAnalyzer
from dotenv import load_dotenv
import logging

# call this when the the program runs
load_dotenv()
logging.getLogger().setLevel(logging.ERROR) # hide warning messages from the Gemini SDK which uses Python's logging module

class AiManager:
    # Composition: The GeminiAiAnalyzer and FallbackAiAnalyzer classes are created and managed internally by AIManager. Their lifecylces are tied to it
    def __init__(self):
        self._gemini_analyzer = GeminiAiAnalyzer() # create an instance of GeminiAIAnalyzer
        self._fallback_analyzer = None # * Haven't create yet
    
    # determine which AI Analyzer to use based on the API status
    def get_analyzer(self):
        api_status = self._gemini_analyzer.check_api_status()
        
        if api_status is True:
            print("Gemini is ready for use...")
            return self._gemini_analyzer
        else:
            return "use FallbackAnalyzer function"
            # return FallbackAnalyzer object

# test code
ai_manager = AiManager()
analyzer = ai_manager.get_analyzer()
ai_output = analyzer.analyze_message("message", "number")