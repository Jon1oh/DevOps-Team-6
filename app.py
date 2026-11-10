from menu.fallback_ai_menu import FallbackAiMenu
from menu.verify_ai_input_menu import VerifyAiInputMenu
from managers.io_manager import IoManager
from managers.ai_manager import AiManager
from managers.data_manager import DataManager
from managers.logic_manager import LogicManager
from storage.json_record_storage import JsonRecordStorage
from storage.record_converter import RecordConverter

class App:
    def __init__(self):
        self.io_manager = IoManager()
        self.ai_manager = AiManager()
        print("Loading Database...")
        self.data_manager = DataManager(JsonRecordStorage())    # records loaded on startup
        if self.data_manager.status_message:                    # when record does not load properly
            print(self.data_manager.status_message)
        else:
            print(f"Database Loaded: {len(self.data_manager.records)} records") 
        self.logic_manager = LogicManager()
        self.fallback_ai_menu = FallbackAiMenu(self.logic_manager, self.ai_manager.get_fallback_analyzer())
        self.verify_ai_input_menu = VerifyAiInputMenu()
    
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
                    record = self.verify_ai_input_menu.check_scam_message_phone_number() # create a Record class if the message and phone number are valid
                    if record is None:
                        continue
                    record.phone_number, record.country_code = self.logic_manager.split_country_code_phone_number(record.phone_number) # split phone number and country code                                        
                    analyzer = self.ai_manager.get_analyzer() # get Gemini analyzer
                    ai_output = analyzer.analyze_message(record) # get Gemini AI output if API is available
                    
                    if ai_output is False:
                        print("Gemini is unavailable.")
                        ai_output = self.fallback_ai_menu.run_fallback_workflow(record)
                        if ai_output == "quit":
                            print("Exiting Program")
                            break
                        elif ai_output is None:
                            continue
                        print("Our Fallback AI model has successfully analyzed the message.")
                    
                    is_valid_ai_output = self.logic_manager.check_ai_output(ai_output)
                    if not is_valid_ai_output:
                        print("One of the fields in the AI output is invalid.")
                        continue
                    
                    print(f"AI analysis completed. Here is the output:\n")                    
                    ai_output = self.logic_manager.format_ai_output(ai_output) # format AI output                    
                    ai_output = self.logic_manager.validate_risk_assessment(ai_output)
                    flagged_number_records = self.data_manager.count_risk_levels(ai_output.phone_number)
                    ai_output = self.logic_manager.escalate_flagged_number(ai_output, flagged_number_records)   
                    self.io_manager.display_message_analysis(ai_output) # _display analysis results for the message
                    saved, message = self.data_manager.save_record(RecordConverter.to_dict(ai_output))

                    if saved:
                        print("New record saved")
                    else:
                        print(f"Could not save record: {message}")
                        
                case _:
                    print("No such case have been created")


app = App()
app.main_loop()
