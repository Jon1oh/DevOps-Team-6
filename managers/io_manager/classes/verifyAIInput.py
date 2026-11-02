from managers.io_manager.classes.menu import menu
import re,phonenumbers

class verifyAIInput(menu):
    def __init__(self):
        super().__init__()
        self.addMenu("Yes")
        self.addMenu("No")
        #this list include the payload to be sent to the AI manager
        self.__AIinputPayload = []
    
    @property
    def AIinputPayload(self):
        return self.__AIinputPayload
    #this method is to add item into the payload list
    
    #this method is to get the scam message content 
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
                    self.__AIinputPayload.append(messageContents)
                    return
            else:
                print("The message cannot only contain digits.")

    #this method is to get the phone number of the scam message 
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
                        self.__AIinputPayload.append(concatMessageSource)
                        return
                    else:
                        print("Invalid phone number try again")
                except phonenumbers.phonenumberutil.NumberParseException:
                    print("Invalid phone number try again")
    
    #this method prints the payload to allow the user to see what information they have entered
    def DisplayPayload(self):
        print("Message Content: " + self.__AIinputPayload[0])
        if len(self.__AIinputPayload) == 2:
            print("Message Source: " + self.__AIinputPayload[1])

    #this method check asks the user to check their input
    def Menuinput(self):
        print("Is this correct?")
        self.DisplayPayload()
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

    #this method check if the scam message content
    def MeaningfulMessage(self,messagecontent):
        words = re.findall(r"[A-Za-z]+", messagecontent)
        total_letters = sum(len(word) for word in words)
        if total_letters >= 4:
            return True
        else:
            return False

    def checkScamMessage_Phonenumber(self):
        while True:
            if self.getScamMessage() == "menu":
                return None
            phonenumberInput = self.getPhoneNumber()
            if phonenumberInput == "menu":
                return None
            elif phonenumberInput == "back":
                self.__AIinputPayload.clear()
                
                continue
            else:
                if self.Menuinput() == 2:
                    self.__AIinputPayload.clear()
                    continue
                else:
                    return self.AIinputPayload