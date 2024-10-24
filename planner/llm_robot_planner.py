from typing import List, Union, Dict
import json

from planner.llm.gen_ai import UnifiedAIRequestHandler

from planner.command.command_base import Command, CommandExecutionResult
from planner.command.command_executor import CommandExecutor

from planner.database.database import DatabaseManager
from planner.database.data_type import TaskRecord
from planner.task_service import TaskService
from planner.result_evaluator import ResultEvaluator

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()
import logging
logger = logging.getLogger("LLMRobotPlanner")


class LLMRobotPlanner():
    """
    全体を処理のフローを制御するクラス
    """
    def __init__(self, api_keys: dict, commands: List[Command]):
        self.llm = UnifiedAIRequestHandler(
            api_keys=api_keys
        )
        self._commands: Dict[str, Command] = {}
        self._db: DatabaseManager = DatabaseManager() 
        self._task_service = TaskService(self.llm, self._db)
        self._cmd_executor = CommandExecutor(self)
        self._result_evaluator = ResultEvaluator(self._db)
        self.register_command(commands)
        
    # TODO: あとで削除
    def _get_all_command_discriptions(self) -> List[str]:
        return [command.discription for command in self._commands.values()]
    
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
        
    def initialize(self, instruction: str):
        """
        初期化
        
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            tasks: List[TaskRecord]
        """
        log.event(
            name="初期化",
            context=f"ユーザーからの指示: {instruction}")
        
        with log.span(name="タスクの分解：") as span:
            span.input(f"指示: {instruction}")
            tasks = self._task_service.split_instruction(instruction)
            span.output("\n".join(f"タスク{i}:\n    タスクの説明: {task.description}\n    タスクの詳細: {task.detail}\n    required_info: {task.required_info}" for i, task in enumerate(tasks, 1)))
        logger.info(
            f"[*]initialize >> create new job\n"
            f"[-]instruction: {instruction}\n"
            f"[-]tasks: {tasks}\n")
        self._db.start_new_job(
            instruction=instruction,
            tasks=tasks)
        
        # TODO: 簡易実装、あとで変更する
        self._db.log_robot_action(
            action="initialize",
            status="succeeded",
            details="ロボットの初期化および行動決定システムの初期化",
            x=None,
            y=None,
            z=None,
            timestamp=None)
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
            with log.action(name="タスクの実行：") as action:
                action.input(f"タスク: {json.dumps(task.to_dict(), indent=4, ensure_ascii=False)}\n")
                # taskの分解
                with log.span(name="コマンドプランニング：") as span:
                    # TODO: 簡易実装、あとで変更する
                    span.input(f"task: {task.description}\ntask detail: {task.detail}\n")
                    action_history = str(json.dumps(self._db.get_all_actions(), indent=4, ensure_ascii=False))
                    commands = self._task_service.split_task(
                        task_description=task.description, 
                        task_detail=task.detail, 
                        cmd_disc_list=self._get_all_command_discriptions(), 
                        action_history=action_history)
                    span.output(f"plan: {json.dumps(commands, indent=4, ensure_ascii=False)}\n")
                
                task.commands = commands
                logger.info(f"task description: {task.description}\n"
                            f"task detail: {task.detail}\n"
                            f"required_info: {task.required_info}")
                for cmdN, cmd in commands.items():
                    logger.info(f"{cmdN}> {cmd['name']}: {cmd['args']}")
                
                # taskの実行
                with log.span(name="コマンドの実行：") as span:
                    span.input(f"commands: {json.dumps(commands, indent=4, ensure_ascii=False)}")
                    # commandの実行
                    for cmdN, cmd in commands.items():
                        cmd_name = cmd["name"]
                        cmd_args = cmd["args"]
                        
                        logger.info(f"[EXEC] {cmdN}: {cmd_name}")
                        exec_result = self._cmd_executor.execute_command(cmd_name, cmd_args)
                        logger.info(f"[RESULT] {exec_result}")
                        self._result_evaluator.evaluate(exec_result)
                        
                    yield commands
                    span.output("成功")
                action.output(f"タスクの実行結果: 成功")
        

        
        