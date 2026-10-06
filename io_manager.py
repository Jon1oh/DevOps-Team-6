import phonenumbers, re
# this file contains the logic regarding user inputs and the main while loop

# Prints the main menu options
def mainMenu_options():
    print(f"\n{'='*36}\nScam Message AI Detector Main Menu\n{'='*36}")
    print("1. Check scam message")
    print("2. View summary of scam messages")
    print("3. Quit\n")

# loop to get and validate the input from the main menu
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
            
# check if the message input contains legitimate words and punctuation, and not just a string of special characters            
def is_meaningful_message(message):
    words = re.findall(r"[A-Za-z]+", message)
    total_letters = sum(len(word) for word in words)
    if total_letters >= 4:
        return True
    else:
        return False
        
# function to get query ai inputs
def inputData_verify():
    while True:
        messageContents = input("Insert message content as one line (or 'menu' to return to main menu):\n") # the message content from the user
        # if statement to check if the string is empty or if the string is just a digit
        if messageContents != "" and messageContents.isdigit() == False:            
            messageContents = re.sub(r'\s+', ' ', messageContents).strip() # this line is to remove >=2 whitespaces in message content
            if not is_meaningful_message(messageContents):
                print("The message must contain meaningful text and not just solely special characters.")
                continue # prompt user for message input again if the message is not meaningful
            # check if the user type quit in message content 
            if messageContents.lower() == 'menu':
                return messageContents
            verifiedPhonenumber = get_Phonenumber()
            if verifiedPhonenumber == "menu":
                return verifiedPhonenumber
            elif verifiedPhonenumber != "back":
                while True:
                    print(f"\n{'='*38}")
                    print("Message Contents: " + messageContents)
                    print("Phone No.: " + verifiedPhonenumber)
                    print("Is that correct?")                    
                    print("1. Yes (Analyse message with AI)")
                    print("2. No (Re-enter Input)")
                    try:
                        checkUserinput = int(input("Please enter 1 or 2: "))
                        if checkUserinput == 1:
                            return [messageContents, verifiedPhonenumber]
                        elif checkUserinput == 2:
                            break # go back to outer loop and re-enter message
                        else:
                            print("Incorrect input. Please enter 1 or 2.\n")
                    except ValueError:
                        print("Incorrect input. Please enter 1 or 2.\n")
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

# this function is ask the user if they want to query the backup ai
def queryAI_Backup():
    print(f"\n{'='*38}")
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
    
    

    
          
    

    