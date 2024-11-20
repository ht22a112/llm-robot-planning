from typing import Dict, List
from planner.command.command_base import Command
class CommandManager():
    def __init__(self) -> None:
        self._commands: Dict[str, Command] = {}
        
    def register_command(self, commands: List[Command]):
        for command in commands:
            if not isinstance(command, Command):
                raise TypeError("command must be subclass of Command")

            command_name = command.name
            if command_name in self._commands:
                raise ValueError(f"command: '{command_name}' is already registered. command name must be unique")
            self._commands[command_name] = command
            
    def _get_command(self, name) -> Command:
        # TODO: 追加の処理を追加する
        return self._commands[name]