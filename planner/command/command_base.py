from typing import Literal, List, Dict
from abc import ABC, abstractmethod
from planner.command.robot_state import RobotState, StateChange
import inspect

import logging
logger = logging.getLogger("LLMCommand")
    
class CommandExecutionResult():
    def __init__(
        self,
        status: Literal["success", "failure"],
        state_changes: List[StateChange] = [],
        details: str = ""
    ) -> None:
        self.cmd_name = ""
        self.cmd_args: Dict[str, str] = {}
        self.status: Literal['success', 'failure'] = status
        self.details: str = details
        self.state_changes: List[StateChange] = state_changes
        
    def __str__(self) -> str:
        return f"[{self.cmd_name}] status: {self.status}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def cmd_name(self) -> str:
        if not self.__cmd_name:
            return "None"
        return self.__cmd_name
    
    @cmd_name.setter
    def cmd_name(self, name: str):
        self.__cmd_name = name    
        

class Command(ABC):
    def __init__(
        self, 
        name: str, 
        description: str,
        state_list: List[RobotState] = [],
        execute_args_description: Dict[str, str] = {},
        execute_required_known_arguments: List[str] = [],
    ) -> None:
        self.__name: str = name
        self.__description: str = description
        self.__state_list: List[RobotState] = state_list
        self.__execute_args_description: Dict[str, str] = execute_args_description
        self.__execute_required_known_args: List[str] = execute_required_known_arguments
        
        if not isinstance(execute_args_description, dict):
            raise TypeError("execute_args_description must be dict")
        if set(execute_args_description.keys()) != set(self.__get_method_arguments('execute')):
            raise ValueError("execute and execute_args_description must be same as method arguments")
        
    @property
    def name(self) -> str:
        '''コマンド名を返す'''
        return self.__name
    
    @property
    def description(self) -> str:
        cmd_name = self.__name
        cmd_description = self.__description
        exec_args_description = self.__execute_args_description
        exec_args_list = self.__get_method_arguments('execute')
        
        args_str = ""
        for exec_arg in exec_args_list:
            arg_desc = exec_args_description[exec_arg]
            args_str += f" {exec_arg}: {arg_desc},"
        args_str = args_str[:-1]
        
        if self.__execute_required_known_args:
            required_args_str = ", ".join(f"<{arg}>" for arg in self.__execute_required_known_args)
            required_args_str += "は既知の内容（ロボットが知っている内容)から同じ単語を選択すること。知らない場合はerrorコマンドを出力する"
        else:
            required_args_str = ""
            
        return f'"{cmd_name}":, args:{args_str}  # {cmd_description} {required_args_str}'
    
    def get_status_list(self):
        return self.__state_list
    
    
    @property
    def required_known_arguments(self) -> list[str]:
        return self.__execute_required_known_args
    
    # TODO: 仮実装なので後々仕様や命名の変更を行う
    def get_knowledge(self, knowledge_name, target):
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> CommandExecutionResult:
        pass
    def on_enter(self):
        pass
    def on_exit(self):
        pass
    
    def __get_method_arguments(self, method_name: str):
        """
        メソッドのselfを除く引数名のリストを返す
        
        Args:
            method_name (str): メソッド名
        returns:
            list[str]: 引数名のリスト
        """
        method = getattr(self, method_name)
        signature = inspect.signature(method)
        return [param.name for param in signature.parameters.values() if param.name != 'self']
    


__all__ = ["Command", "CommandExecutionResult", "StateChange"]