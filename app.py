import managers.io_manager as io_manager, managers.ai_manager as ai_manager, managers.logic_manager as logic_manager, managers.data_manager as data_manager, models.fallback_ai as fallback_ai

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
            data_manager.load_records()
        case 1:
            verifiedInputdata =  io_manager.inputData_verify() # prompt user for message content and phone number
            message = verifiedInputdata[0]
            phone_number_with_country_code = verifiedInputdata[1]
            final_ai_output = None

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
                        # print(ai_output)
                        
                        # Call fallback AI bot
                        phone_number, country_code = logic_manager.split_country_code_phone_number(phone_number_with_country_code)
                        final_ai_output = fallback_ai.analyse_message(message, phone_number, country_code) 
                        print(final_ai_output)
                        
            else: # when the AI model returns a valid JSON object
                is_valid_ai_output = logic_manager.check_ai_output(ai_output)
                if is_valid_ai_output:
                    print(f"AI analysis completed. Here is the output:\n")                    
                    final_ai_output= logic_manager.format_ai_output(ai_output) # format AI output
                                        
                else:
                    print("One of the fields in the AI output is invalid.")

            
            # after getting the JSON object from the Gemini/Custom AI API
            if final_ai_output:
                flagged_number_records = data_manager.count_risk_levels(final_ai_output["phone_number"])
                final_ai_output = logic_manager.escalate_flagged_number(final_ai_output, flagged_number_records)
                
                if logic_manager.validate_scam_indicators(final_ai_output):
                    io_manager.display_message_analysis(final_ai_output) # display analysis results for the message
                    # TODO: Write JSON object to DB
                    
                    data_manager.save_record(final_ai_output)
                    print("record saved")    
                