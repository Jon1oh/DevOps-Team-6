from abc import ABC, abstractmethod
import re

class menu(ABC):
    def __init__(self):
        self.__menu = []
        
    def addMenu(self,text):
        self.__menu.append(text)
    def display(self):
        for each in self.__menu:
            print(str(self.__menu.index(each)) + ". " + each)
    def Menuinput(self):
        pass

class mainMenu(menu):
    def __init__(self):
        super().__init__()
    def display(self):
        print(f"\n{'='*36}\nScam Message AI Detector Main Menu\n{'='*36}")
        return super().display()
    def Menuinput(self):
        while True:
            try:
                userinput = int(input("Please Choose a number between 1-3"))
                if userinput < 4 and userinput > 0:
                    return userinput
                else:
                    print("Please input 1,2 or 3")
            except ValueError:
                print("Incorrect input please try again")
                
class ScamDetectorMenu(menu):
    def __init__(self):
        super().__init__()
    def Menuinput(self):
        while True:
            try:
                userinput = int(input("Please Choose a number between 1-3"))
                if userinput < 3 and userinput > 0:
                    return userinput
                else:
                    print("Please input 1,2")
            except ValueError:
                print("Incorrect input please try again")
    def scamMessage(self):
        while True:
            messageContents = input("Insert message content as one line (or 'menu' to return to main menu):\n") # the message content from the user                    messageContents = re.sub(r'\s+', ' ', messageContents).strip()
            if messageContents.lower() == 'menu':
                return messageContents.lower()
            # if statement to check if the string is empty or if the string is just a digit
            elif messageContents != "" and messageContents.isdigit() == False:
                if not self.MeaningfulMessage(messageContents):
                    print("The message must contain meaningful text and not just solely special characters.")
                    continue # prompt user for message input again if the message is not meaningful
            else:
                print("The message cannot only contain digits.")
            
    def MeaningfulMessage(message):
        words = re.findall(r"[A-Za-z]+", message)
        total_letters = sum(len(word) for word in words)
        if total_letters >= 4:
            return True
        else:
            return False