from abc import ABC, abstractmethod

class AiAnalyzer(ABC):
    
    @abstractmethod
    def analyze_message(self, messaege, phone_number, country_code=None): # only country_code is used by FallbackAiAnalyze, but both Gemini and FallbackAi Analyzers will use this same interface
        pass # each analyzer class will have their own version of this function
    
    def get_analyzer_name(self):
        pass