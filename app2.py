import managers.io_manager as io_manager, managers.ai_manager as ai_manager, managers.logic_manager as logic_manager, managers.data_manager as data_manager, models.fallback_ai as fallback_ai
from datetime import datetime
from managers.io_managerClass import mainMenu,verifyAIInput

# loads the records upon startup
print("\nLoading database...")
records = data_manager.load_records()
print("Database loaded successfully.")

# main loop of program
while True:
    DefaultMenu = mainMenu()
    DefaultMenu.display()
    match DefaultMenu.Menuinput(): # a match case to match the output of menu to correct action
        case 3:
            print("Exiting Program")
            break
        case 2:
            # call the message summary function
            records = data_manager.load_records()
            summary = data_manager.summary_with_percentages(records)
            io_manager.print_message_summary(summary)
        case 1:
            while True:
                GetUserAIInput = verifyAIInput()
                if GetUserAIInput.getScamMessage() == "menu":
                    break
                phonenumberInput = GetUserAIInput.getPhoneNumber()
                if phonenumberInput == "menu":
                    break
                elif phonenumberInput == "back":
                    continue
                else:
                    GetUserAIInput.Menuinput