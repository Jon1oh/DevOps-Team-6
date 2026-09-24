# this file contains the logic regarding user inputs and the main while loop

#Prints the main menu options
def mainMenu_options():
    print("1. Check scam message")
    print("2. View historical analysis")
    print("3. quit")
    
    
#loop to get and validate the input from the main menu
def mainMenu_Input():
    while True:
        try:
            userInput = int(input("Please choose an option(1,2,3):"))
            if userInput > 0 and userInput < 4:
                return userInput
            else:
                print("Incorrect input try again.")
        except ValueError:
            print("Incorrect input try again.")
            
#function to query 
def queryAI_Input():
    while True:
        #variable holds the content of the message
        messageContents = input("Paste message content or quit:\n")
        if messageContents != "" and messageContents.isdigit() == False:
            if messageContents.lower() == 'quit':
                return messageContents
            messageSource = input("Source of the message, quit or back: ")
            if messageSource.lower() == "quit":
                return messageSource
            elif(messageSource.lower() != "back"):
                return {"messageContents":messageContents, "messageSource":messageSource}
        else:
            print("Do not leave the message contents blank or just a number")
        
#main loop of program
while True:
    mainMenu_options()
    mainMenu_choice = mainMenu_Input()
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
            
        
    

    