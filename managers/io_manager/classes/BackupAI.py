from managers.io_manager.classes.menu import menu

class BackupAI(menu):
    def __init__(self):
        super().__init__()
        print(f"\n{'='*38}")
        print("Our primary AI API failed to respond in a timely manner")        
        print("What do you want to do?:")
        self.addMenu("1. Analyse message with backup AI model")
        self.addMenu("2. Return to main menu")
        
    def Menuinput(self):
        try:
            userInput = int(input("Please Choose a number between 1 to " + str(super().menulength)+ ": "))
            #check if the input is between 1-x where x is length of the list
            if userInput > 0 and (super().menulength + 1):
                return userInput
            else:
                print("Incorrect input try again.")
        except ValueError:
            print("Incorrect input try again.")
