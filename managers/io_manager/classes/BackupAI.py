from managers.io_manager.classes.Menu import Menu

class BackupAI(Menu):
    def __init__(self):
        super().__init__()
        print(f"\n{'='*38}")
        print("Our primary AI API failed to respond in a timely manner")        
        print("What do you want to do?:")
        self.add_menu("Analyse message with backup AI model")
        self.add_menu("Return to main menu")
        
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
