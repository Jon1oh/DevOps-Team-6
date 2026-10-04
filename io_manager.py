import phonenumbers, re
# this file contains the logic regarding user inputs and the main while loop

#Prints the main menu options
def mainMenu_options():
    print(f"\n{'='*36}\nScam Message AI Detector Main Menu\n{'='*36}")
    print("1. Check scam message")
    print("2. View summary of scam messages")
    print("3. Quit\n")

#loop to get and validate the input from the main menu
def mainMenu_Input():
    #while  loop to check user inputs
    while True:
        mainMenu_options()
        #try except statement to check if the input can be type casted to interger if valueerror will print then run throgh the loop again
        try:
            userInput = int(input("Please choose an option(1, 2, 3): "))
            #check if the input is between 1-3
            if userInput > 0 and userInput < 4:
                return userInput
            else:
                print("Incorrect input try again.")
        except ValueError:
            print("Incorrect input try again.")
        
#function to get query ai inputs
def inputData_verify():
    while True:
        messageSource = []
        #variable holds the content of the message
        messageContents = input("Insert message content (or 'menu' to return to main menu):\n")
        #if statement to check if the string is empty or if the string is just a digit
        if messageContents != "" and messageContents.isdigit() == False:
            #this line is to remove >=2 whitespaces in message content
            messageContents = re.sub(r'\s+', ' ', messageContents).strip()
            #check if the user type quit in message content
            if messageContents.lower() == 'menu':
                return messageContents
            verifiedPhonenumber = get_Phonenumber()
            if verifiedPhonenumber == "menu":
                return verifiedPhonenumber
            elif verifiedPhonenumber != "back":
                print("=========================================")
                print("Message Contents: " + messageContents)
                print("Phone No.: " + verifiedPhonenumber )
                print("Is that correct? ")
                print("1. Yes (Analyse message with AI)")
                print("2. No (Re-enter Input)")
                try:
                    checkUserinput = int(input("Please enter 1 or 2: "))
                    if checkUserinput == 1:
                        return [messageContents, verifiedPhonenumber]
                    elif checkUserinput < 1 or checkUserinput > 2:
                        print("Incorrect input try again.")
                except ValueError:
                    print("Incorrect input try again.")
        else:
            print("The message cannot be blank or just a number. Please try again.")

def get_Phonenumber():
    while True:
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
                    return concatMessageSource
                else:
                    print("Invalid phone number try again")
            except phonenumbers.phonenumberutil.NumberParseException:
                print("Invalid phone number try again")

#this function is ask the user if they want to query the backup ai
def queryAI_Backup():
    print("============================================================")
    print("Our primary AI API failed to respond in a timely manner")        
    print("What do you want to do?:")
    print("1. Analyse message with backup AI model")
    print("2. Return to main menu")
    print("3. Quit program")
    try:
        userInput = int(input("Please choose an option(1, 2, 3): "))
        #check if the input is between 1-3
        if userInput > 0 and userInput < 4:
            return userInput
        else:
            print("Incorrect input try again.")
    except ValueError:
        print("Incorrect input try again.")
    
    

    
          
    

    