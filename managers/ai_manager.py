from analyzers.gemini_analyzer import GeminiAiAnalyzer
from analyzers.fallback_ai_analyzer import FallbackAiAnalyzer

class AiManager:
    # Composition: The GeminiAiAnalyzer and FallbackAiAnalyzer classes are created and managed internally by AIManager. Their lifecylces are tied to it
    def __init__(self):
        self._gemini_analyzer = GeminiAiAnalyzer() # create an instance of GeminiAIAnalyzer
        self._fallback_analyzer = FallbackAiAnalyzer() # create an instance of FallbackAiAnalyzer
    
    # determine which AI Analyzer to use based on the API status
    def get_analyzer(self):
        api_status = self._gemini_analyzer.check_api_status()
        
        if api_status is True:
            print("Gemini is ready for use...")
            return self._gemini_analyzer
        else:
            print("Reverting to fallback AI")
            return self._fallback_analyzer