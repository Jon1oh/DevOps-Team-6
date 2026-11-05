from managers.io_manager.classes.menu import Menu
from managers.io_manager.io_manager import FallbackAiMenu, VerifyAiInputMenu
import managers.ai_manager as ai_manager
import managers.data_manager as data_manager
import managers.logic_manager as logic_manager
import emoji

class App(Menu):
    def __init__(self):
        super().__init__()
        self.add_menu("Check Scam Message")
        self.add_menu("View summary of scam messages")
        self.add_menu("quit")

    def _display(self):
        print(f"\n{'='*36}\nScam Message AI Detector Main Menu\n{'='*36}")
        return super()._display()
    
    def _menu_input(self):
        while True:
            try:
                user_input = int(input("Please Choose a number between 1 to " + str(super().menulength)+ ": "))
                if user_input > 0 and user_input < (super().menulength + 1):
                    return user_input
                else:
                    print("Please input a number between 1 and " + str(super().menulength))
            except ValueError:
                print("Incorrect input please try again")
                
    def _display_message_analysis(self, ai_output):
        print(f"\n{'='*38}SCAM MESSAGE ANALYSIS RESULT{'='*38}\n")

        # _display message based on risk level of message
        if ai_output.risk_level == "HIGH" or ai_output.risk_level == "MEDIUM":
            print(f"{emoji.emojize(':warning: POTENTIAL SCAM DETECTED')}\n")
        else:
            print(f"{emoji.emojize(':check_mark_button: MESSAGE APPEARS SAFE')}\n")
        
        print(f"Risk Level: {ai_output.risk_level}")
        print(f"Scam Probability: {ai_output.scam_probability}")
        print(f"Scam Type: {ai_output.scam_type}")
        
        print(f"Phone number: {ai_output.phone_number}")
        print(f"Country code: {ai_output.country_code}")
        
        # Indicators section
        if type(ai_output.indicators) is list:
            print("\nIndicators:")        
            for i in ai_output.indicators:
                print(f"- {i}")
        else:
            print(f"\nIndicators: {ai_output.indicators}")
        
        # Explanation section
        print("\nExplanation:")
        print(ai_output.explanation)
        
        # Recommendation section
        print("\nRecommendation:")
        print(ai_output.recommendation)
        print(f"{'='*38}")
    
    def _print_message_summary(self, summary: dict) -> None:
        """Print the summary returned by summary_with_percentages()."""
        print("\n==============================")
        print("      SCAM MESSAGE SUMMARY")
        print("==============================\n")
        print(f"Total messages: {summary['total_messages']}")

        print("\nRisk Level Breakdown")
        print("------------------------------")
        for risk_level, count in summary["risk_level_breakdown"].items():
            percent = summary["risk_level_percentage"].get(risk_level, 0)
            print(f"{risk_level}: {count} ({percent}%)")

        print("\nScam Category Breakdown")
        print("------------------------------")
        for scam_type, count in summary["scam_category_breakdown"].items():
            percent = summary["scam_category_percentage"].get(scam_type, 0)
            print(f"{scam_type}: {count} ({percent}%)")

        print("\nCountry of Origin Breakdown")
        print("------------------------------")
        for country_code, count in summary["origin_country_breakdown"].items():
            percent = summary["origin_country_percentage"].get(country_code, 0)
            label = summary["origin_country_labels"][country_code]
            print(f"{label}: {count} ({percent}%)")

        print("\nMost Common type of Scam")
        print("------------------------------")
        print(summary["most_common_scam"])

    def main_loop(self):
        while True:
            self._display()
            # a match case to match the output of menu to correct action
            match self._menu_input(): 
                #this case will exit the program
                case 3:
                    print("Exiting Program")
                    break
                #this case will print the summary of all scam message checked with our program
                case 2:
                    # call the message summary function
                    records = data_manager.load_records()
                    summary = data_manager.summary_with_percentages(records)
                    self._print_message_summary(summary)
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
                                self._display_message_analysis(final_ai_output) # _display analysis results for the message
                                data_manager.save_record(final_ai_output)
                                print("New record saved")    
                            else:
                                print("\nSorry, our Custom AI bot was unable to derive an accurate analysis of your message.")
                case _:
                    print("No such case have been created")


app = App()
app.main_loop()
