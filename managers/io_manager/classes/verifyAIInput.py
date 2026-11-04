from managers.io_manager.classes.Menu import Menu
import re
import phonenumbers

class VerifyAIInput(Menu):
    def __init__(self):
        super().__init__()
        self.add_menu("Yes")
        self.add_menu("No")
        #this list include the payload to be sent to the AI manager
        self.__ai_input_payload = []
    
    @property    
    def ai_input_payload(self):
        return self.__ai_input_payload     
    #this method prints the payload to allow the user to see what information they have entered
    def _display_payload(self):
        print("Message Content: " + self.__ai_input_payload[0])
        if len(self.__ai_input_payload) == 2:
            print("Message Source: " + self.__ai_input_payload[1])
    
    #this method is to get the scam message content 
    def _get_scam_message(self):
        while True:
            message_contents = input("Insert message content as one line (or 'menu' to return to main menu):\n") # the message content from the user                    
            message_contents = re.sub(r'\s+', ' ', message_contents).strip()
            if message_contents.lower() == 'menu':
                return message_contents.lower()
            # if statement to check if the string is empty or if the string is just a digit
            elif message_contents != "" and message_contents.isdigit() == False:
                if not self._meaningful_message(message_contents):
                    print("The message must contain meaningful text and not just solely special characters.")
                    continue # prompt user for message input again if the message is not meaningful
                else: 
                    self.__ai_input_payload.append(message_contents)
                    return
            else:
                print("The message cannot only contain digits.")

    #this method is to get the phone number of the scam message 
    def _get_phone_number(self):
        while True:
            self._display_payload()
            unverified_phone_number = input("Enter the phone number with country code ('menu' to return to main menu, or 'back' to go back): ")
            if unverified_phone_number.lower() == "menu" or unverified_phone_number.lower() == "back":
                return unverified_phone_number.lower()
            else:
                if "+" not in unverified_phone_number:
                    unverified_phone_number = "+" + unverified_phone_number.replace(" ", "")
                    
                try:
                    phone_number = phonenumbers.parse(unverified_phone_number, None)
                    if phonenumbers.is_possible_number(phone_number):
                        phone_number = "+"+str(phone_number.country_code) + str(phone_number.national_number)
                        self.__ai_input_payload.append(phone_number)
                        return
                    else:
                        print("Invalid phone number try again")
                except phonenumbers.phonenumberutil.NumberParseException:
                    print("Invalid phone number try again")
    
    #this method check asks the user to check their input
    def menu_input(self):
        print("Is this correct?")
        self._display_payload()
        self.display()
        while True:
            try:
                user_input = int(input("Please Choose a number between 1 to " + str(super().menulength)+ ": "))
                if user_input > 0 and user_input < (super().menulength + 1):
                    return user_input
                else:
                    print("Please input a number between 1 and " + str(super().menulength))
            except ValueError:
                print("Incorrect input please try again")

    #this method check if the scam message content
    def _meaningful_message(self,message_content):
        words = re.findall(r"[A-Za-z]+", message_content)
        total_letters = sum(len(word) for word in words)
        if total_letters >= 4:
            return True
        else:
            return False

    def check_scam_message_phone_number(self):
        while True:
            if self._get_scam_message() == "menu":
                return None
            phone_number_input = self._get_phone_number()
            if phone_number_input == "menu":
                return None
            elif phone_number_input == "back":
                self.__ai_input_payload.clear()
                
                continue
            else:
                if self.menu_input() == 2:
                    self.__ai_input_payload.clear()
                    continue
                else:
                    return self.__ai_input_payload