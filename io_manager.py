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
            

        
#main loop of program
while True:
    mainMenu_options()
    mainMenu_choice = mainMenu_Input()

            