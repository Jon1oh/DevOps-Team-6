from interfaces.menu import Menu
from analyzers.fallback_ai_analyzer import FallbackAiAnalyzer
from managers.logic_manager import LogicManager
from models.record import Record

class FallbackAiMenu(Menu):
    def __init__(self, logic_manager: LogicManager, fallback_ai_analyzer: FallbackAiAnalyzer):
        super().__init__()
        self.logic_manager = logic_manager
        self.fallback_ai_analyzer = fallback_ai_analyzer
        self.add_menu("Analyse message with backup AI model")
        self.add_menu("Return to main menu")
        self.add_menu("Quit")
        
    def menu_input(self):
        while True:
            try:
                user_input = int(input("Please Choose a number between 1 to " + str(super().menulength)+ ": "))
                #check if the input is between 1-x where x is length of the list
                if user_input > 0 and user_input < (super().menulength + 1):
                    return user_input
                else:
                    print("Incorrect input try again.")
            except ValueError:
                print("Incorrect input try again.")

    def run_fallback_workflow(self, record: Record):
        print(f"\n{'='*38}")
        print("Our primary AI API failed to respond in a timely manner")        
        print("What do you want to do?:")
        self.display()
        # match case for backup ai to see if go to mainmenu, query backup or quit
        match self.menu_input(): 
            case 3:
                return "quit"
            case 2:
                return None
            case 1:
                print("Using our In-House-Trained Custom AI Bot. It can make mistakes. Please verify important info.")
                ai_output = self.fallback_ai_analyzer.analyze_message(record) 
                return ai_output
            case _:
                print("No such case have been created")