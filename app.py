import managers.ai_manager as ai_manager, managers.logic_manager as logic_manager, managers.data_manager as data_manager, models.fallback_ai as fallback_ai
from datetime import datetime
from managers.io_manager.io_manager import BackupAI, mainMenu, verifyAIInput


# loads the records upon startup
print("\nLoading database...")
records = data_manager.load_records()
print("Database loaded successfully.")

# main loop of program
while True:
    DefaultMenu = mainMenu()
    DefaultMenu.display()
    
    # a match case to match the output of menu to correct action
    match DefaultMenu.Menuinput(): 
        
        #this case will exit the program
        case 3:
            print("Exiting Program")
            break
        
        #this case will print the summary of all scam message checked with our program
        case 2:
            # call the message summary function
            records = data_manager.load_records()
            summary = data_manager.summary_with_percentages(records)
            DefaultMenu.print_message_summary(summary)
        
        #this case will prompt the user to enter the scam message
        case 1:
            getUserAIInput = verifyAIInput()
            scamMessageContent = getUserAIInput.checkScamMessage_Phonenumber()
            if scamMessageContent != None:
                message, phone_number_with_country_code = scamMessageContent[0],scamMessageContent[1]
                ai_output = ai_manager.analyse_message(message, phone_number_with_country_code)
                if ai_output == False: # call backup AI bot when the AI model API fails
                    backupAI = BackupAI()

                    match backupAI.Menuinput(): # match case for backup ai to see if go to mainmenu or query backup
                        case 2:
                            break
                        case 1:
                            print("Using our In-House-Trained Custom AI Bot. It can make mistakes. Please verify important info.")
                            phone_number, country_code = logic_manager.split_country_code_phone_number(phone_number_with_country_code)
                            ai_output = fallback_ai.analyse_message(message, phone_number, country_code) 
                            if "timestamp" not in ai_output:
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # format timestamp as YYYY-MM-DD HH:MM:SS
                                ai_output = {"timestamp": timestamp, **ai_output}
                                final_ai_output = logic_manager.format_ai_output(ai_output)
                            
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
                                    logic_manager.validate_scam_probability(final_ai_output)
                                    DefaultMenu.display_message_analysis(final_ai_output) # display analysis results for the message
                                    data_manager.save_record(final_ai_output)
                                    print("New record saved")    
                                else:
                                    print("\nSorry, our Custom AI bot was unable to derive an accurate analysis of your message.")
                        case _:
                            print("No such case have been created")
        case _:
            print("No such case have been created")