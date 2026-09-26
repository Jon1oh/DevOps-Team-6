import phonenumbers
import re
# this file contains the logic regarding user inputs and the main while loop

#Prints the main menu options
def mainMenu_options():
    print("=================================")
    print("1. Check scam message")
    print("2. View historical analysis")
    print("3. quit\n")

#loop to get and validate the input from the main menu
def mainMenu_Input():
    #while  loop to check user inputs
    while True:
        mainMenu_options()
        #try except statement to check if the input can be type casted to interger if valueerror will print then run throgh the loop again
        try:
            userInput = int(input("Please choose an option(1,2,3):"))
            #check if the input is between 1-3
            if userInput > 0 and userInput < 4:
                return userInput
            else:
                print("Incorrect input try again.")
        except ValueError:
            print("Incorrect input try again.")
        
#function to get query ai inputs
def queryAI_Input():
    while True:
        messageSource = []
        #variable holds the content of the message
        messageContents = input("Paste message content or quit:\n")
        #if statement to check if the string is empty or if the string is just a digit
        if messageContents != "" and messageContents.isdigit() == False:
            #this line is to remove empty string 
            messageContents = re.sub(r'\s+', ' ', messageContents).strip()
            #check if the user type quit in message content
            if messageContents.lower() == 'quit':
                return messageContents
            verifiedPhonenumber = getPhonenumber()
            if verifiedPhonenumber == "quit":
                return verifiedPhonenumber
            elif verifiedPhonenumber != "back":
                return [messageContents,verifiedPhonenumber]
        else:
            print("Do not leave the message contents blank or just a number")

def getPhonenumber():
    while True:
        unverifiedMessageSource = input("Enter the phone number with country code, quit or back: ")
        if unverifiedMessageSource.lower() == "quit" or unverifiedMessageSource.lower() == "back":
            return unverifiedMessageSource.lower()
        else:
            if "+" not in unverifiedMessageSource:
                unverifiedMessageSource = "+" + unverifiedMessageSource.replace(" ", "")
                
            try:
                messageSource = phonenumbers.parse(unverifiedMessageSource,None)
                if phonenumbers.is_possible_number(messageSource):
                    concatMessageSource = "+"+str(messageSource.country_code) + str(messageSource.national_number)
                    return concatMessageSource
                else:
                    print("invalid phone number try again")
            except phonenumbers.phonenumberutil.NumberParseException:
                print("invalid phone number try again")

#this function is ask the user if they want to query the backup ai
def queryAIFail():
    print("============================================================")
    print("Our primary AI API failed to respond in a timely manner")        
    print("use backup AI or return to main menu?:")
    print("1.Use backup AI")
    print("2.Return to main menu")
    print("3.Quit program")
    try:
        userInput = int(input("Please choose an option(1,2,3):"))
        #check if the input is between 1-3
        if userInput > 0 and userInput < 4:
            return userInput
        else:
            print("Incorrect input try again.")
    except ValueError:
        print("Incorrect input try again.")
    
    

    
          
    

    