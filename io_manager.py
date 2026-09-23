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
        messageContents = input("Paste message content or quit:\n")
        sourceContents = ""
        if messageContents != "" and messageContents.isdigit() == False:
            if messageContents.lower() == 'quit':
                return messageContents
            sourceContents = input("Source of the message, quit or back: ")
            if sourceContents.lower() == "quit":
                return sourceContents
            elif(sourceContents.lower() != "back"):
                return {"messageContents":messageContents, "sourceContents":sourceContents}
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
            
        
    

    