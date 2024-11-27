from planner.command.command_base import Command, CommandExecutionResult
from planner.command.manager import CommandManager
from planner.database.data_type import CommandRecord
from utils.utils import to_json_str

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class CommandExecutor:
    def __init__(self, command_manager: CommandManager):
        self._cmd_manager: CommandManager = command_manager

    def execute_command(self, command: CommandRecord) -> CommandExecutionResult:
        """
        コマンドを実行する
        
        Args:
            command_name: 実行するコマンド名
            args: dict[str, Any] 
                {
                    "arg1_name": "value",
                    "arg2_name": "value"
                }
            
        Returns:
            CommandExecutionResult
        """
        
        command_name = command.description
        args = command.args
        
        with log.action(f"コマンド: {command_name}") as action:
            action.input("args: " + to_json_str(args))
            cmd = self._cmd_manager.get_command(command_name)
            # コマンドの実行
            cmd.on_enter()
            exec_result = cmd.execute(**args)
            exec_result.cmd_name = command_name
            exec_result.cmd_args = args
            cmd.on_exit()
            action.output(f"result: {exec_result}")

        return exec_result