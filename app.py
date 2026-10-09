import io_manager, ai_manager, logic_manager, data_manager, fallback_ai

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
            message = verifiedInputdata[0]
            phone_number_with_country_code = verifiedInputdata[1]

            # pass user message and phone number to API first
            ai_output = ai_manager.analyse_message(message, phone_number_with_country_code) # pass message content and phone number to ai_manager
            
            # check the ai output from the model
            if ai_output == False: # call backup AI bot when the AI model API fails
                backupAI = io_manager.queryAI_Backup()
                match backupAI: # match case for backup ai to see if quit, go to mainmenu or query backup
                    case 3:
                        print("Exiting Program")
                        break
                    case 1:
                        print(ai_output)
                        phone_number, country_code = logic_manager.split_country_code_phone_number(phone_number_with_country_code)
                        fallback_ai_output = fallback_ai.analyse_message(message, phone_number, country_code) 
                        print(fallback_ai_output)
                        
            else: # when the AI model returns a valid JSON object
                is_valid_ai_output = logic_manager.check_ai_output(ai_output)
                if is_valid_ai_output:
                    print(f"AI analysis completed. Here is the output:\n")
                    
                    # format and display formatted AI analysis output of message and write to DB
                    formatted_ai_output = logic_manager.format_ai_output(ai_output)
                    
                    # check if number was flagged out in a High Risk Incident before
                    flagged_number_records = data_manager.count_risk_levels(formatted_ai_output["phone_number"])
                    formatted_ai_output = logic_manager.escalate_flagged_number(ai_output, flagged_number_records)
                    
                    if logic_manager.validate_scam_indicators(formatted_ai_output):
                        io_manager.display_message_analysis(formatted_ai_output)
                        # TODO call db_manager to store the ai output in DB
                else:
                    print("One of the fields in the AI output is invalid.")
