from menu.fallback_ai_menu import FallbackAiMenu
from menu.verify_ai_input_menu import VerifyAiInputMenu
from managers.io_manager import IoManager
from managers.ai_manager import AiManager
from managers.data_manager import DataManager
from managers.logic_manager import LogicManager
from storage.json_record_storage import JsonRecordStorage

class App:
    def __init__(self):
        self.io_manager = IoManager()
        self.ai_manager = AiManager()
        self.data_manager = DataManager(JsonRecordStorage())
        self.logic_manager = LogicManager()
        self.fallback_ai_menu = FallbackAiMenu()
    
    def main_loop(self):             
        while True:
            self.io_manager.display()
            # a match case to match the output of menu to correct action
            match self.io_manager.menu_input(): 
                #this case will exit the program
                case 3:
                    print("Exiting Program")
                    break
                case 2:
                    # call the message summary function                    
                    summary = self.data_manager.summary()
                    self.io_manager.print_message_summary(summary)
                #this case will prompt the user to enter the scam message
                case 1:
                    record = VerifyAiInputMenu().check_scam_message_phone_number()
                    final_ai_output = None
                    if record != None:
                        message, phone_number_with_country_code = record.message, record.phone_number
                        message_analyzer = self.ai_manager.get_analyzer() # either get Gemini or Fallback AI. Depending on Gemini API status
                        phone_number, country_code = self.logic_manager.split_country_code_phone_number(phone_number_with_country_code) # split phone number and country code
                        ai_output = message_analyzer.analyze_message(message, phone_number, country_code) # get the Record object
                        if ai_output == False: # call backup AI bot when the AI model API fails
                            fallback_ai_output = self.fallback_ai_menu.run_fallback_workflow(message, phone_number_with_country_code)
                            if fallback_ai_output == "quit":
                                print("Exiting Program")
                                break
                            elif fallback_ai_output is None: 
                                continue
                            else:
                                final_ai_output = fallback_ai_output
                                print("Our backup AI has successfully analyzed the message.")
                        else: # when the AI model returns a valid JSON object
                            is_valid_ai_output = self.logic_manager.check_ai_output(ai_output)
                            if is_valid_ai_output:
                                print(f"AI analysis completed. Here is the output:\n")                    
                                final_ai_output= self.logic_manager.format_ai_output(ai_output) # format AI output                 
                            else:
                                print("One of the fields in the AI output is invalid.")
                        # after getting the JSON object from the Gemini/Custom AI API
                        if final_ai_output:
                            flagged_number_records = self.data_manager.count_risk_levels(final_ai_output.phone_number)
                            final_ai_output = self.logic_manager.escalate_flagged_number(final_ai_output, flagged_number_records)   
                            if self.logic_manager.validate_risk_assessment(final_ai_output):
                                self.io_manager.display_message_analysis(final_ai_output) # _display analysis results for the message
                                self.data_manager.save_record(final_ai_output)
                                print("New record saved")    
                            else:
                                print("\nSorry, our Custom AI bot was unable to derive an accurate analysis of your message.")
                case _:
                    print("No such case have been created")


app = App()
app.main_loop()
