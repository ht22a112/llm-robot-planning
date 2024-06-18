from typing import Literal
from abc import ABC, abstractmethod


class CommandExecutionResult():
    def __init__(self, status: Literal["succeeded", "failed"]) -> None:
        self.status: Literal['succeeded', 'failed'] = status
    
    def __str__(self) -> str:
        return f"status: {self.status}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
class CommandBase(ABC):
    def __init__(
        self, 
        name, 
        discription
    ) -> None:
        self.__name = name
        self.__discription = discription
        
    def get_name(self) -> str:
        '''コマンド名を返す'''
        return self.__name
    
    def get_command_discription(self) -> str:
        return self.__discription
    
    @abstractmethod
    def execute(self) -> CommandExecutionResult:
        pass
    
    def on_enter(self):
        pass
        
    def on_exit(self):
        pass
    
    
    
    
