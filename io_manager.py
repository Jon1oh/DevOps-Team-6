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
        #variable holds the content of the message
        messageContents = input("Paste message content or quit:\n")
        #if statement to check if the string is empty or if the string is just a digit
        if messageContents != "" and messageContents.isdigit() == False:
            #check if the user type quit in message content
            if messageContents.lower() == 'quit':
                return messageContents
            messageSource = input("Source of the message, quit or back: ")
            #check if user type quit in message source
            if messageSource.lower() == "quit":
                return messageSource
            #check if user did not type back
            elif(messageSource.lower() != "back"):
                return {"messageContents":messageContents, "messageSource":messageSource}
        else:
            print("Do not leave the message contents blank or just a number")
        
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
            
        
    

    