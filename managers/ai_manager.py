from app.analyzers.gemini_analyzer import GeminiAiAnalyzer
from app.analyzers.fallback_ai_analyzer import FallbackAiAnalyzer
from dotenv import load_dotenv
import logging

# call this when the the program runs
load_dotenv()
logging.getLogger().setLevel(logging.ERROR) # hide warning messages from the Gemini SDK which uses Python's logging module

class AiManager:
    # Composition: The GeminiAiAnalyzer and FallbackAiAnalyzer classes are created and managed internally by AIManager. Their lifecylces are tied to it
    def __init__(self):
        self._gemini_analyzer = GeminiAiAnalyzer() # create an instance of GeminiAIAnalyzer
        self._fallback_analyzer = FallbackAiAnalyzer() # create an instance of FallbackAiAnalyzer
    
    # return Gemini Analyzer class as the main analyzer
    def get_analyzer(self):
        return self._gemini_analyzer
    
    # let other classes borrow/use the fallback analyzer class that AiManager owns, instead of creating a new one
    def get_fallback_analyzer(self):
        return self._fallback_analyzer