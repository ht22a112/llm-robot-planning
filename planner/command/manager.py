from typing import Dict, List
from planner.command.command_base import Command
from planner.command.robot_state import RobotState, StateChange

class RobotStateManager():
    def __init__(self) -> None:
        self._states: Dict[str, RobotState] = {}

    def register_states(self, states: List[RobotState]):
        for state in states:
            if not isinstance(state, RobotState):
                raise TypeError("command_state must be RobotState class")            
            state_name = state.name
            if state_name in self._states:
                raise ValueError(f"RobotState: '{state_name}' is already registerd. command state must be unique")
            self._states[state_name] = state
            
    def get_all(self) -> list[RobotState]:
        # TODO: 改善
        return list(self._states.values())
    
    def update(self, changes: List[StateChange]):
        for change in changes:
            if change.name not in self._states:
                raise ValueError(f"RobotState: '{change.name}' is not registered. RobotState must be registered")
            self._states[change.name].update(change)
    
    # --- デバッグ用 ---
    def print_all(self):
        # TODO: 改善、または削除
        for state in self._states.values():
            print(f"{state.name}: {state.description}, active: {state.active}, args: {state.args}")
            
class CommandManager():
    def __init__(self) -> None:
        self._commands: Dict[str, Command] = {}

    def register_commands(self, commands: List[Command]):
        for command in commands:
            if not isinstance(command, Command):
                raise TypeError("command must be subclass of Command")
            command_name = command.name
            if command_name in self._commands:
                raise ValueError(f"command: '{command_name}' is already registered. command name must be unique")
            self._commands[command_name] = command

    def get_all_command_descriptions(self) -> List[str]:
        # TODO: 改善
        return [command.description for command in self._commands.values()]
        
    def get_command(self, name) -> Command:
        # TODO: 追加の処理を追加する
        return self._commands[name]
    
   