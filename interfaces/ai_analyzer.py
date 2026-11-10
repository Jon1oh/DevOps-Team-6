from abc import ABC, abstractmethod
from models.record import Record

class AiAnalyzer(ABC):
    
    @abstractmethod
    def analyze_message(self, record: Record): # only country_code is used by FallbackAiAnalyze, but both Gemini and FallbackAi Analyzers will use this same interface
        pass # each analyzer class will have their own version of this function
