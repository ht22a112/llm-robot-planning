from typing import List, Union, Dict
import json

from llm.gen_ai import UnifiedAIRequestHandler
from planner.command_base import CommandBase, CommandExecutionResult

from database.database import DatabaseManager, Task
from database.message import *

from prompts.utils import get_prompt

from llm.logger import log_llm
import logging
logger = logging.getLogger("LLMRobotPlanner")

class LLMRobotPlanner():
    def __init__(self, api_keys: dict, commands: List[CommandBase]):
        self.chat_ai = UnifiedAIRequestHandler(
            api_keys=api_keys
        )
        self._commands: Dict[str, CommandBase] = {}
        self._db: DatabaseManager = DatabaseManager() 

        self.register_command(commands)
    
    def register_command(self, commands: List[CommandBase]):
        for command in commands:
            if not isinstance(command, CommandBase):
                raise TypeError("command must be subclass of CommandBase")
            
            command_name = command.name
            if command_name in self._commands:
                raise ValueError(f"command: '{command_name}' is already registered. command name must be unique")
            self._commands[command_name] = command
            
    def _get_all_command_discriptions(self) -> List[str]:
        return [command.discription for command in self._commands.values()]
    
    def _get_all_knowledge_names(self) -> List[str]:
        return ["オブジェクト（物、物体）の位置", "場所の位置情報", "周囲に居る人の性別および名前に関する情報", "自身の過去の行動に関する情報"]
    def _get_command(self, name) -> CommandBase:
        # TODO: 追加の処理を追加する
        return self._commands[name]
        
    def initialize(self, instruction: str):
        """
        初期化
        
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            tasks: List[Task]
        """
        
        tasks = self.split_instruction(instruction)
        
        logger.info(
            f"[*]initialize >> create new job\n"
            f"[-]instruction: {instruction}\n"
            f"[-]tasks: {tasks}\n"
        )
        
        self._db.start_new_job(
            instruction=instruction,
            tasks=tasks
        )
        
        return tasks
        

    def process(self):
        """
        ロボットに与える命令を処理
        
        Args:
            None
        
        Returns:
            None
        """
        current_job = self._db.get_current_job()
        if current_job is None:
            raise ValueError("no current job")
        
        tasks = current_job.tasks
        
        # tasksの実行
        for task in tasks:
            # taskの分解
            commands = self.split_task(task.description, task.detail)
            task.commands = commands
            logger.info(f"task description: {task.description}\n"
                        f"task detail: {task.detail}\n"
                        f"required_info: {task.required_info}")
            for cmdN, cmd in commands.items():
                logger.info(f"{cmdN}> {cmd['name']}: {cmd['args']}")
                
            # commandの実行
            for cmdN, cmd in commands.items():
                cmd_name = cmd["name"]
                cmd_args = cmd["args"]
                
                logger.info(f"[EXEC] {cmdN}: {cmd_name}")
                exec_result = self.execute_command(cmd_name, cmd_args)
                logger.info(f"[RESULT] {exec_result}")
                
            yield commands
    
    from logger.logger import FunctionLogger
    @FunctionLogger.log_function
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
        cmd = self._get_command(command_name)
        # コマンドの実行
        cmd.on_enter()
        exec_result = cmd.execute(**args)
        exec_result.cmd_name = command_name
        exec_result.cmd_args = args
        cmd.on_exit()
        
        return exec_result
    
    def split_task(self, task_description: str, task_detail: str) -> dict:
        
        # コマンド一覧の生成
        command_discription = self._get_all_command_discriptions()
        result = ""
        for idx, content in enumerate(command_discription, 1):
            if idx == 1:
                result += f"{idx}: {content}\n"
            else:
                result += f"    {idx}: {content}\n"
        command_discription = result
        
        prompt = get_prompt(
            prompt_name="split_task",
            replacements={
                "task_description": task_description,
                "task_detail": task_detail,
                "command_discription": command_discription
            },
            symbol=("{{", "}}")
        )
        
        response = self.chat_ai.generate_content_v2(
            prompt=prompt, 
            response_type="json", 
            convert_type="dict",
            model_name=None
        )
        log_llm(response, prompt)
        return response
        
        
        
    def split_instruction(self, instruction: str) -> List[Task]:
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            List[Task]: ロボットに与える命令のリスト
        """
        
        obtainable_information_list = "".join(f'・{name}\n' for name in self._get_all_knowledge_names())
        prompt = get_prompt(
            prompt_name="split_instruction",
            replacements={
                "obtainable_information_list": str(obtainable_information_list),
                "instruction": instruction,
            },
            symbol=("{{", "}}")
        )
        
        response = self.chat_ai.generate_content_v2(
            prompt=prompt,
            response_type="json",
            convert_type="dict",
            model_name=None
        )
        log_llm(response, prompt)
            
        return [
            Task(
                description=task.get("description"), 
                detail=task.get("detail"),
                required_info=task.get("required information")
            ) for task in response["tasks"].values()
        ]