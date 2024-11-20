# from __future__ import annotations # python ver3.7 ~ 3.10は必要
from planner.command.command_base import Command, CommandExecutionResult
from planner.database.data_type import CommandRecord
import planner.llm_robot_planner as _root
from utils.utils import to_json_str

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class CommandExecutor:
    def __init__(self, controller: '_root.LLMRobotPlanner'):
        self._controller: '_root.LLMRobotPlanner' = controller
        
    def _get_command(self, name) -> Command:
        return self._controller._commands[name]
    
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
            cmd = self._get_command(command_name)
            # コマンドの実行
            cmd.on_enter()
            exec_result = cmd.execute(**args)
            exec_result.cmd_name = command_name
            exec_result.cmd_args = args
            cmd.on_exit()
            action.output(f"result: {exec_result}")

        return exec_result