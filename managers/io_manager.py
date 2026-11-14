import re
import phonenumbers
# Import your helpers and models

#this class handles all input validation and output of the application
class IoManager:
    #this method checks if the phone number is valid
    def validate_number(self,number:str)-> phonenumbers.PhoneNumber:
        if "+" not in number:
            number = "+" + number.replace(" ", "")
        try:
            parsed_number = phonenumbers.parse(number, None)
            print(parsed_number)
        except phonenumbers.NumberParseException as error:
            raise ValueError("Enter a valid international phone number.") from error
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("Enter a valid international phone number")
        return parsed_number
    
    #this method splits the phonenumber to country code and phone number
    def split_number(self,number:str) ->tuple[str,str]:
        parsed_number =self.validate_number(number)
        country_code = f"+{parsed_number.country_code}"
        local_number = str(parsed_number.national_number)
        return local_number, country_code 
            
    #this method is used to parse the message before it is sent to the ai
    def parse_message(self,message:str)->str:
        message = re.sub(r'\s+', ' ', message).strip()
        words = re.findall(r"[A-Za-z]+", message)
        total_letters = sum(len(word) for word in words)
        if total_letters >= 8:
            return message
        else:
            raise ValueError