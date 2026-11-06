from abc import ABC, abstractmethod

class AiAnalyzer(ABC):
    
    @abstractmethod
    def analyze_message(self):
        pass # each analyzer class will have their own version of this function