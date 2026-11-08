from managers.io_manager.classes.menu import Menu
import emoji

class io_manager(Menu):
    def __init__(self):
        super().__init__()
        self.add_menu("Check Scam Message")
        self.add_menu("View summary of scam messages")
        self.add_menu("quit")

    def display(self):
        print(f"\n{'='*36}\nScam Message AI Detector Main Menu\n{'='*36}")
        return super().display()
    
    def menu_input(self):
        while True:
            try:
                user_input = int(input("Please Choose a number between 1 to " + str(super().menulength)+ ": "))
                if user_input > 0 and user_input < (super().menulength + 1):
                    return user_input
                else:
                    print("Please input a number between 1 and " + str(super().menulength))
            except ValueError:
                print("Incorrect input please try again")
                
    def display_message_analysis(self, ai_output):
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
    
    def print_message_summary(self, summary: dict) -> None:
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