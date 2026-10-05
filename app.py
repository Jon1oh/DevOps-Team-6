import io_manager, ai_manager

# main loop of program
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
                verifiedInputdata =  io_manager.inputData_verify() # prompt user for message content and phone number
                print("query ai now")
                # TODO call AI manager to analyse message
                ai_manager.analyse_message(verifiedInputdata[0], verifiedInputdata[1]) # pass message content and phone number to AI manager
                print(verifiedInputdata) # the message content and phone number in a list from io_manager
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
                            #call the backup ai with the queryoutput as
                            #call the AI_MANAGER
                            #if query ai fail give choice to 
                        