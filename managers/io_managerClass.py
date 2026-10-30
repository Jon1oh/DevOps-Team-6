from abc import ABC, abstractmethod
import re,phonenumbers

class menu(ABC):
    def __init__(self):
        self.__menu = []

    @property
    def menulength(self):
        return len(self.__menu)   
    def addMenu(self,text):
        self.__menu.append(text)
    def display(self):
        for each in self.__menu:
            print(str(self.__menu.index(each) + 1) + ". " + each)
    @abstractmethod
    def Menuinput(self):
        pass

class mainMenu(menu):
    def __init__(self):
        super().__init__()
        self.addMenu("Check Scam Message")
        self.addMenu("View summary of scam messages")
        self.addMenu("quit")

    def display(self):
        print(f"\n{'='*36}\nScam Message AI Detector Main Menu\n{'='*36}")
        return super().display()
    def Menuinput(self):
        while True:
            try:
                userinput = int(input("Please Choose a number between 1 to " + str(super().menulength)+ ": "))
                if userinput > 0 and userinput < (super().menulength + 1):
                    return userinput
                else:
                    print("Please input a number between 1 and " + str(super().menulength))
            except ValueError:
                print("Incorrect input please try again")
                
class verifyAIInput(menu):
    def __init__(self):
        super().__init__()
        self.__AIinputPayload = []
    def addPayload(self,Content):
        self.__AIinputPayload.append(Content)
    def getScamMessage(self):
        while True:
            messageContents = input("Insert message content as one line (or 'menu' to return to main menu):\n") # the message content from the user                    
            messageContents = re.sub(r'\s+', ' ', messageContents).strip()
            if messageContents.lower() == 'menu':
                return messageContents.lower()
            # if statement to check if the string is empty or if the string is just a digit
            elif messageContents != "" and messageContents.isdigit() == False:
                if not self.MeaningfulMessage(messageContents):
                    print("The message must contain meaningful text and not just solely special characters.")
                    continue # prompt user for message input again if the message is not meaningful
                else: 
                    self.addPayload(messageContents)
            else:
                print("The message cannot only contain digits.")

    def getPhoneNumber(self):
        while True:
            self.DisplayPayload()
            unverifiedMessageSource = input("Enter the phone number with country code ('menu' to return to main menu, or 'back' to go back): ")
            if unverifiedMessageSource.lower() == "menu" or unverifiedMessageSource.lower() == "back":
                return unverifiedMessageSource.lower()
            else:
                if "+" not in unverifiedMessageSource:
                    unverifiedMessageSource = "+" + unverifiedMessageSource.replace(" ", "")
                    
                try:
                    messageSource = phonenumbers.parse(unverifiedMessageSource, None)
                    if phonenumbers.is_possible_number(messageSource):
                        concatMessageSource = "+"+str(messageSource.country_code) + str(messageSource.national_number)
                        self.addPayload[concatMessageSource]
                        return concatMessageSource
                    else:
                        print("Invalid phone number try again")
                except phonenumbers.phonenumberutil.NumberParseException:
                    print("Invalid phone number try again")

    def DisplayPayload(self):
        print("Message Content: " + self.__AIinputPayload[0])
        if len(self.__AIinputPayload) == 2:
            print("Message Source: " + self.__AIinputPayload[1])

    def Menuinput(self):
        self.addMenu("Yes")
        self.addMenu("No")
        self.display()
        while True:
            try:
                userinput = int(input("Please Choose a number between 1 to " + str(super().menulength)+ ": "))
                if userinput > 0 and userinput < (super().menulength + 1):
                    return userinput
                else:
                    print("Please input a number between 1 and " + str(super().menulength))
            except ValueError:
                print("Incorrect input please try again")

    
    def MeaningfulMessage(self,messagecontent):
        words = re.findall(r"[A-Za-z]+", messagecontent)
        total_letters = sum(len(word) for word in words)
        if total_letters >= 4:
            return True
        else:
            return False



