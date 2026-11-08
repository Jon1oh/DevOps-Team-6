from managers.io_manager.classes.Menu import Menu
import managers.logic_manager as logic_manager
import models.fallback_ai as fallback_ai
from datetime import datetime

class FallbackAiMenu(Menu):
    def __init__(self):
        super().__init__()
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

    def run_fallback_workflow(self,message,phone_number_with_country_code):
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
                phone_number, country_code = logic_manager.split_country_code_phone_number(phone_number_with_country_code)
                ai_output = fallback_ai.analyse_message(message, phone_number, country_code) 
                if "timestamp" not in ai_output:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # format timestamp as YYYY-MM-DD HH:MM:SS
                    ai_output = {"timestamp": timestamp, **ai_output}
                    return logic_manager.format_ai_output(ai_output)
                else:
                    return ai_output
            case _:
                print("No such case have been created")