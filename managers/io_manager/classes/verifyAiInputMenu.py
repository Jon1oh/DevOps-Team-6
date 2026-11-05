from managers.io_manager.classes.menu import Menu
from record import Record
import re, phonenumbers

class VerifyAiInputMenu(Menu):
    def __init__(self):
        super().__init__()
        #this list include the payload to be sent to the AI manager
        self.add_menu("Yes")
        self.add_menu("No")
        self._record = Record() # create a Record object to store the scam message information
    
    #this method prints the payload to allow the user to see what information they have entered
    def _display_payload(self):
        if self._record.message:
            print("Message Content: " + self._record.message)
            if self._record.phone_number:
                print("Message Source: " + self._record.phone_number)
    
    #this method is to get the scam message content 
    def _get_scam_message(self):
        while True:
            message = input("Insert message content as one line (or 'menu' to return to main menu):\n") # the message content from the user                    
            message = re.sub(r'\s+', ' ', message).strip()
            if message.lower() == 'menu':
                return message.lower()
            # if statement to check if the string is empty or if the string is just a digit
            elif message != "" and message.isdigit() == False:
                if not self._meaningful_message(message):
                    print("The message must contain meaningful text and not just solely special characters.")
                    continue # prompt user for message input again if the message is not meaningful
                else: 
                    self._record.message = message
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
                        self._record.phone_number = phone_number
                        return
                    else:
                        print("Invalid phone number try again")
                except phonenumbers.phonenumberutil.NumberParseException:
                    print("Invalid phone number try again")
    
    #this method check asks the user to check their input
    def _menu_input(self):
        print("Is this correct?")
        self._display_payload()
        self._display()
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
                self._record = Record() # reset the record object to clear the previous message content
                continue
            else:
                if self._menu_input() == 2:
                    self._record = Record() # reset the record object to clear the previous message content
                    continue
                else:
                    return self._record