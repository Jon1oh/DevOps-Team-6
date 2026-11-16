from abc import ABC, abstractmethod

class Menu(ABC):
    def __init__(self):
        self.__menu = []

    @property
    def menulength(self):
        return len(self.__menu)  
     
    def add_menu(self,text):
        self.__menu.append(text)
        
    def display(self):
        for each in self.__menu:
            print(str(self.__menu.index(each) + 1) + ". " + each)
            
    @abstractmethod
    def menu_input(self):
        pass