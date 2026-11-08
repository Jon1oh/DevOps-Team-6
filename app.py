import logging
from dotenv import load_dotenv
from managers.io_manager import io_manager
from menu.fallback_ai_menu import FallbackAiMenu
from menu.verify_ai_input_menu import VerifyAiInputMenu
import managers.ai_manager as ai_manager
import managers.data_manager as data_manager
import managers.logic_manager as logic_manager



class App:
    def __init__(self):
        self.__Mainmenu = io_manager()
    
    def main_loop(self):
        load_dotenv()
        logging.getLogger().setLevel(logging.ERROR) # hide warning messages from the Gemini SDK which uses Python's logging module   
             
        while True:
            self.__Mainmenu.display()
            # a match case to match the output of menu to correct action
            match self.__Mainmenu.menu_input(): 
                #this case will exit the program
                case 3:
                    print("Exiting Program")
                    break
                case 2:
                    # call the message summary function
                    records = data_manager.load_records()
                    summary = data_manager.summary_with_percentages(records)
                    self.__Mainmenu.print_message_summary(summary)
                #this case will prompt the user to enter the scam message
                case 1:
                    record = VerifyAiInputMenu().check_scam_message_phone_number()
                    final_ai_output = None
                    if record != None:
                        message, phone_number_with_country_code = record.message, record.phone_number
                        ai_output = ai_manager.analyse_message(message, phone_number_with_country_code)
                        if ai_output == False: # call backup AI bot when the AI model API fails
                            fallback_ai = FallbackAiMenu()
                            fallback_ai_output = fallback_ai.run_fallback_workflow(message, phone_number_with_country_code)
                            if fallback_ai_output == "quit":
                                print("Exiting Program")
                                break
                            elif fallback_ai_output is None: 
                                continue
                            else:
                                final_ai_output = fallback_ai_output
                                print("Our backup AI has successfully analyzed the message.")
                        else: # when the AI model returns a valid JSON object
                            is_valid_ai_output = logic_manager.check_ai_output(ai_output)
                            if is_valid_ai_output:
                                print(f"AI analysis completed. Here is the output:\n")                    
                                final_ai_output= logic_manager.format_ai_output(ai_output) # format AI output                 
                            else:
                                print("One of the fields in the AI output is invalid.")
                        # after getting the JSON object from the Gemini/Custom AI API
                        if final_ai_output:
                            flagged_number_records = data_manager.count_risk_levels(final_ai_output.phone_number)
                            final_ai_output = logic_manager.escalate_flagged_number(final_ai_output, flagged_number_records)   
                            if logic_manager.validate_scam_indicators(final_ai_output):
                                logic_manager.validate_scam_probability(final_ai_output)
                                self.__Mainmenu.display_message_analysis(final_ai_output) # _display analysis results for the message
                                data_manager.save_record(final_ai_output)
                                print("New record saved")    
                            else:
                                print("\nSorry, our Custom AI bot was unable to derive an accurate analysis of your message.")
                case _:
                    print("No such case have been created")


app = App()
app.main_loop()
