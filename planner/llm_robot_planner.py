from typing import List, Union, Dict

from planner.llm.gen_ai import UnifiedAIRequestHandler

from planner.command.command_base import Command, CommandExecutionResult
from planner.command.command_executor import CommandExecutor

from planner.database.database import DatabaseManager
from planner.database.data_type import TaskRecord
from planner.task_service import TaskService
from planner.result_evaluator import ResultEvaluator

from utils.utils import to_json_str

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()
import logging
logger = logging.getLogger("LLMRobotPlanner")


class LLMRobotPlanner():
    """
    全体を処理のフローを制御するクラス
    """
    def __init__(self, api_keys: dict, commands: List[Command]):
        self._llm = UnifiedAIRequestHandler(
            api_keys=api_keys
        )
        self._commands: Dict[str, Command] = {}
        self._db: DatabaseManager = DatabaseManager() 
        self._task_service = TaskService(self._llm, self._db)
        self._cmd_executor = CommandExecutor(self)
        self._result_evaluator = ResultEvaluator(self._db)
        
        #  TODO: テスト
        from planner.rag import RAG
        self._rag = RAG(self._db, self._llm)
        
        self.register_command(commands)

        
    def init_helper(self):
        """テスト用初期化メソッド"""
        self._db.init_helper()
        
        
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
        with log.span(name="初期化：") as span:
            span.input(f"ユーザーからの指示: {instruction}")
            self.init_helper()
            span.output("初期化完了")
            
        
        with log.span(name="タスクの分解：") as span:
            span.input(f"指示: {instruction}")
            tasks = self._task_service.interpret_instruction(instruction)
            span.output("\n".join(f"タスク{i}:\n    タスクの説明: {task.content}\n    タスクの詳細: {task.details}" for i, task in enumerate(tasks, 1)))
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
            status="success",
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
                action.input(f"タスク: {task.to_json_str()}")
                
                # TODO: RAGテスト
                with log.span(name="RAGのテスト：") as span:
                    span.input(f"task: {task.content}")             
                    r = self._rag._retrieval_document(task.content)
                    span.output(f"result: {to_json_str(r)}")
                    
                # taskの分解（コマンドプランニング）
                with log.span(name="コマンドプランニング：") as span:
                    # TODO: 簡易実装、あとで変更する
                    span.input(f"task: {task.content}\ntask detail: {task.details}")
                    action_history_json = to_json_str(self._db.get_all_actions())
                    action_history_json = "\n".join(" " * 8 + line for line in action_history_json.splitlines())
                    commands = self._task_service.generate_command_calls(
                        task_description=task.content, 
                        task_detail=task.details, 
                        cmd_disc_list=self._get_all_command_discriptions(), 
                        action_history=action_history_json,
                        knowledge=r)
                    span.output(f"plan: {to_json_str(commands)}")
                
                task.commands = commands
                logger.info(f"task description: {task.content}\n"
                            f"task detail: {task.details}\n")
                for cmd in commands:
                    logger.info(f"{cmd.sequence_number}> {cmd.content}: {cmd.args}")
                
                # taskの実行（コマンドの実行）
                with log.span(name="コマンドの実行：") as span:
                    span.input(f"commands: {to_json_str(commands)}")
                    # commandの実行
                    for cmd in commands:
                        cmd_name = cmd.content
                        cmd_args = cmd.args
                        
                        logger.info(f"[EXEC] {cmd}: {cmd_name}")
                        exec_result = self._cmd_executor.execute_command(cmd_name, cmd_args)
                        logger.info(f"[RESULT] {exec_result}")
                        self._result_evaluator.evaluate(exec_result)
                        
                    yield commands
                    span.output("成功")
                action.output(f"タスクの実行結果: 成功")
        

        
        