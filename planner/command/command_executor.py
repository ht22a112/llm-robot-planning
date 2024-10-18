# from __future__ import annotations # python ver3.7 ~ 3.10は必要
import json

from planner.command.command_base import Command, CommandExecutionResult
import planner.llm_robot_planner as _root
from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class CommandExecutor:
    def __init__(self, controller: '_root.LLMRobotPlanner'):
        self._controller: '_root.LLMRobotPlanner' = controller
        
    def _get_command(self, name) -> Command:
        return self._controller._commands[name]
    
    def execute_command(self, command_name: str, args: dict) -> CommandExecutionResult:
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
        with log.action(f"コマンド: {command_name}") as action:
            action.input("args: " + json.dumps(args, indent=2, ensure_ascii=False))
            cmd = self._get_command(command_name)
            # コマンドの実行
            cmd.on_enter()
            exec_result = cmd.execute(**args)
            exec_result.cmd_name = command_name
            exec_result.cmd_args = args
            cmd.on_exit()
            action.output(f"result: {exec_result}")

        return exec_result