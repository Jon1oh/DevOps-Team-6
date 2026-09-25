import phonenumbers
# this file contains the logic regarding user inputs and the main while loop

#Prints the main menu options
def mainMenu_options():
    print("1. Check scam message")
    print("2. View historical analysis")
    print("3. quit")
    
    
#loop to get and validate the input from the main menu
def mainMenu_Input():
    #while  loop to check user inputs
    while True:
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
            
#function to query 
def queryAI_Input():
    while True:
        messageSource = []
        #variable holds the content of the message
        messageContents = input("Paste message content or quit:\n")
        #if statement to check if the string is empty or if the string is just a digit
        if messageContents != "" and messageContents.isdigit() == False:
            #check if the user type quit in message content
            if messageContents.lower() == 'quit':
                return messageContents
            verifiedPhonenumber = getPhonenumber()
            if verifiedPhonenumber == "quit":
                return verifiedPhonenumber
            elif verifiedPhonenumber != "back":
                #messageSource.append(verifiedPhonenumber.country_code)
                #messageSource.append(verifiedPhonenumber.national_number)
                #print(messageSource)
                return [messageContents,verifiedPhonenumber.country_code,verifiedPhonenumber.national_number]
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
                    print(messageSource)
                    return messageSource
                else:
                    print("invalid phone number try again")
            except phonenumbers.phonenumberutil.NumberParseException:
                print("invalid phone number try again")

#main loop of program
while True:
    mainMenu_options()
    #this variable holds the verified userinput
    mainMenu_choice = mainMenu_Input()
    #a match case to match the output of menu to correct action
    match mainMenu_choice:
        case 3:
            print("Exiting Program")
            break
        case 2:
            #call the historical analysis function
            print("case 2")
        case 1:
            queryOutput =  queryAI_Input()
            if queryOutput != "quit":
                print("query ai now")
            print(queryOutput)
            #call the AI_MANAGER
            
        
    

    