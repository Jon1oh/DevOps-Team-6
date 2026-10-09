#this File contains the main loop of the program
#imported files
import io_manager

#main loop of program
while True:
    #this variable holds the verified userinput
    mainMenu_choice = io_manager.mainMenu_Input()
    #a match case to match the output of menu to correct action
    match mainMenu_choice:
        case 3:
            print("Exiting Program")
            break
        case 2:
            #call the message summary function
            print("case 2")
        case 1:
            verifiedInputdata =  io_manager.inputData_verify()
            if verifiedInputdata != "menu":
                print("query ai now")
                # TODO call AI manager to analyse message
                print(verifiedInputdata)
                mainAIoutput = "" #TODO CHANGE TO AI API CALL
                if mainAIoutput == False:
                    backupAI = io_manager.queryAI_Backup()
                    #match case for backup ai to see if quit, go to mainmenu or query backup
                    match backupAI:
                        case 3:
                            print("Exiting Program")
                            break
                        case 1:
                            print(mainAIoutput) 
                            # store message, phone number and country code in separate variables to pass backup ai                                                  
                            # call the backup ai with the queryoutput as
                            # call the AI_MANAGER
                            # if query ai fail give choice to 
                        