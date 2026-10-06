import io_manager, ai_manager, logic_manager

# main loop of program
while True:
    mainMenu_choice = io_manager.mainMenu_Input() # this variable holds the verified userinput
    match mainMenu_choice: # a match case to match the output of menu to correct action
        case 3:
            print("Exiting Program")
            break
        case 2:
            # call the message summary function
            print("case 2")
        case 1:
            verifiedInputdata =  io_manager.inputData_verify() # prompt user for message content and phone number
            print("query ai now")
            ai_output = ai_manager.analyse_message(verifiedInputdata[0], verifiedInputdata[1]) # pass message content and phone number to ai_manager
            # print(verifiedInputdata) # the message content and phone number in a list from io_manager
            
            # check the ai output from the model
            if ai_output == False: # call backup AI bot when the AI model API fails
                backupAI = io_manager.queryAI_Backup()
                match backupAI: # match case for backup ai to see if quit, go to mainmenu or query backup
                    case 3:
                        print("Exiting Program")
                        break
                    case 1:
                        print(ai_output)
                        #call the backup ai with the queryoutput as
                        #call the AI_MANAGER
                        #if query ai fail give choice to 
            else: # when the AI model returns a valid JSON object
                is_valid_ai_output = logic_manager.check_ai_output_fields(ai_output)
                if is_valid_ai_output:
                    print(f"AI analysis completed. Here is the output:\n")
                    # TODO display formatted AI analysis output of message
                    formatted_ai_output = logic_manager.format_ai_output(ai_output)
                    # TODO call db_manager to store the ai output in DB
                else:
                    pass