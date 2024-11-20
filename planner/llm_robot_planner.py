from typing import List, Union, Dict, Tuple, Optional, Literal
from datetime import datetime, timezone

from planner.llm.gen_ai import UnifiedAIRequestHandler

from planner.command.command_base import Command, CommandExecutionResult
from planner.command.executor import CommandExecutor
from planner.command.manager import CommandManager
from planner.database.database import DatabaseManager
from planner.database.data_type import TaskRecord, CommandRecord, JobRecord, CommandExecutionResultRecord
from planner.task_service import TaskService
from planner.result_evaluator import ResultEvaluator, EvaluatorResult, ReplanningData

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
        
        self._db: DatabaseManager = DatabaseManager() 
        self._task_service = TaskService(self._llm, self._db)
        self._cmd_manager = CommandManager()
        self._cmd_executor = CommandExecutor(self._cmd_manager)
        self._result_evaluator = ResultEvaluator(self._db, self._llm)
        
        #  TODO: テスト
        from planner.rag import RAG
        self._rag = RAG(self._db, self._llm)
        
        self._cmd_manager.register_command(commands)

    def init_helper(self):
        """テスト用初期化メソッド"""
        self._db.init_helper()
        
        
    # TODO: あとで削除
    def _get_all_command_descriptions(self) -> List[str]:
        return [command.description for command in self._commands.values()]
    
        
    def initialize(self):
        """
        システムの初期化

        Returns:
            tasks: List[TaskRecord]
        """
        with log.span(name="初期化：") as span:
            span.input(f"初期化開始")
            #self.init_helper()
            span.output("初期化完了")
    
    def _start_job(self, instruction: str, additional_info: str) -> JobRecord:
        """
        ジョブの開始
        
        Args:
            instruction: str ユーザーからの指示（ロボットに与える命令）
            additional_info: str 追加情報 (指示に関する補足情報)
            
        Returns:
            job_id: int ジョブID
        """
        with log.span(name="プランニング開始："):
            current_job_record = self._db.add_job(
                JobRecord(
                    description=instruction,
                    additional_info=additional_info
                )
            )
        return current_job_record
        
        
    def _generate_tasks(
        self, 
        job: JobRecord
    ) -> List[TaskRecord]:
        with log.span(name="タスクの生成：") as span:
            span.input(f"指示: {job.description}")
            
            # タスクの生成
            tasks = self._task_service.generate_tasks(job.description)
            
            # タスクをデータベースに登録
            self._db.add_tasks_to_job(tasks=tasks, job_id=job.uid)
            
            span.output("\n".join(f"タスク{i}:\n    タスクの説明: {task.description}\n    タスクの詳細: {task.additional_info}" for i, task in enumerate(tasks, 1)))
            logger.info(
                f"[*]initialize >> create new job\n"
                f"[-]instruction: {job.description}\n"
                f"[-]tasks: {tasks}\n")
        
            # # TODO: 簡易実装、あとで変更する
            # self._db.add_command_execution_result(
            #     action="initialize",
            #     status="success",
            #     details="ロボットの初期化および行動決定システムの初期化",
            #     x=None,
            #     y=None,
            #     z=None,
            #     timestamp=None)
        return tasks
    
    
    def _regenerate_tasks(
        self, 
        job: JobRecord,
        replanning_data: ReplanningData
    ) -> List[TaskRecord]:
        with log.span(name="タスクの生成：") as span:
            span.input(f"指示: {job.description}")
            
            # タスクの生成
            tasks = self._task_service.reinterprete_instruction(job.description, replanning_data)
            
            # タスクをデータベースに登録
            self._db.add_tasks_to_job(tasks=tasks, job_id=job.uid)
            
            span.output("\n".join(f"タスク{i}:\n    タスクの説明: {task.description}\n    タスクの詳細: {task.additional_info}" for i, task in enumerate(tasks, 1)))
            logger.info(
                f"[*]initialize >> create new job\n"
                f"[-]instruction: {job.description}\n"
                f"[-]tasks: {tasks}\n")
        
            # # TODO: 簡易実装、あとで変更する
            # self._db.add_command_execution_result(
            #     action="initialize",
            #     status="success",
            #     details="ロボットの初期化および行動決定システムの初期化",
            #     x=None,
            #     y=None,
            #     z=None,
            #     timestamp=None)
        return tasks
    
    def _generate_commands(
        self,
        task: TaskRecord,
    ):
        # taskからCommand listの生成（コマンドプランニング）
        with log.span(name="コマンドプランニング：") as span:
            span.input(f"task: {task.description}\ntask detail: {task.additional_info}")
            
            # TODO: RAGテスト
            with log.span(name="RAGのテスト：") as span:
                span.input(f"task: {task.description}")   
                doc = self._rag._retrieval_document(task.description)
                span.output(f"result: {to_json_str(doc)}")
            
            # 情報の取得
            # コマンドの生成
            commands = self._task_service.generate_command_calls(
                task,
                command_description_list=self._get_all_command_descriptions(), 
                command_history=self._db.get_all_actions(),
                knowledge=doc)
            
            # データベースにコマンドを登録
            self._db.add_commands_to_task(commands, task.uid)
        
            span.output(f"plan: {to_json_str(commands)}")
            logger.info(f"task description: {task.description}\n"
                        f"task detail: {task.additional_info}\n")
            for cmd in commands:
                logger.info(f"{cmd.sequence_number}> {cmd.description}: {cmd.args}")
        return commands
    
    def regenerate_commands(
        self,
        task: TaskRecord,
        replanning_data: ReplanningData
    ):
        # taskからCommand listの生成（コマンドプランニング）
        with log.span(name="コマンドプランニング：") as span:
            span.input(f"task: {task.description}\ntask detail: {task.additional_info}")
            
            # TODO: RAGテスト
            with log.span(name="RAGのテスト：") as span:
                span.input(f"task: {task.description}")   
                doc = self._rag._retrieval_document(task.description)
                span.output(f"result: {to_json_str(doc)}")
            
            # 情報の取得
            # コマンドの生成
            commands = self._task_service.regenerate_command_calls(
                task=task, 
                replanning_data=replanning_data,
                command_description_list=self._get_all_command_descriptions(), 
                command_history=self._db.get_all_actions(),
                knowledge=doc
            )
            
            # データベースにコマンドを登録
            self._db.add_commands_to_task(commands, task.uid)
        
            span.output(f"plan: {to_json_str(commands)}")
            logger.info(f"task description: {task.description}\n"
                        f"task detail: {task.additional_info}\n")
            for cmd in commands:
                logger.info(f"{cmd.sequence_number}> {cmd.description}: {cmd.args}")
        return commands
    
    def _execute_command(self, command: CommandRecord) -> CommandRecord:
        """
        引数に与えられたCommandRecordに対応するコマンドを実行して、そのコマンド実行結果を記録する
        
        Args:
            command: CommandRecord
        
        Returns:
            CommandRecord: 実行結果を含むCommandRecord
        """
        # コマンドの実行
        start_time = datetime.now(timezone.utc)
        cmd_result = self._cmd_executor.execute_command(command)
        
        # コマンドの実行結果の記録
        cmd_exec_result_record = CommandExecutionResultRecord(
            timestamp=start_time,
            start_time=start_time,
            end_time=datetime.now(timezone.utc),
            status=cmd_result.status,
            detailed_info=cmd_result.details,
        )
        command.execution_result = cmd_exec_result_record
        command.status = cmd_result.status
        self._db.add_command_execution_result(
            command_execution_result_record=cmd_exec_result_record,
            command_id=command.uid
        )
        self._db.update_command(command)
        return command
    
    def _execute_command_list(
        self, 
        task, 
        commands: List[CommandRecord]
    ) -> Union[
        Tuple[Literal[False], EvaluatorResult], 
        Tuple[Literal[True], None]
    ]:
        with log.span(name="コマンドリストの実行：") as span:
            span.input(f"commands: {to_json_str(commands)}")
            for cmd in commands:
                # コマンドの実行                        
                exec_result = self._execute_command(cmd)
                
                # コマンドの実行結果の評価および分析
                evaluate_result = self._result_evaluator.evaluate_execution_command_result(task, cmd)
                if evaluate_result["is_replanning_needed"]:
                    # replanning
                    span.output(f"失敗")
                    return (False, evaluate_result)
            else:
                span.output("成功")
                return (True, None)

        
    def _execute_task(
        self, 
        task: TaskRecord
    ) -> Tuple[bool, Optional[EvaluatorResult]]:
        
        with log.action(name="タスクの実行：") as action:
            action.input(f"タスク: {task.to_json_str()}")

            # コマンドリストの生成
            commands = self._generate_commands(task)
            # コマンドリストの実行
            is_successful, evaluate_result = self._execute_command_list(task, commands)
            
            while True:
                if is_successful and evaluate_result is None:
                    # コマンドリストの実行が成功した場合
                    action.output("成功")
                    return (is_successful, evaluate_result)
                else:
                    # コマンドリストの実行が失敗（リプランニングが必要）
                    assert evaluate_result is not None
                    
                    # リプランニングデータの選択
                    replanning_data = evaluate_result["replanning_data"]["1"]
        
                    # -- リプランニング --
                    # 未実行のコマンドのstatusを"canceled"に変更
                    for command in commands:
                        if command.status == "pending":
                            command.status = "canceled"
                            self._db.update_command(command)
                            
                    if replanning_data["replanning_level"] == "command_level":
                        # コマンドレベルのリプランニング
                        commands = self.regenerate_commands(task, replanning_data)
                        is_successful, evaluate_result = self._execute_command_list(task, commands)
                    elif replanning_data["replanning_level"] == "task_level":
                        # タスクレベルのリプランニング
                        action.output("失敗")
                        return (False, evaluate_result)
                    else:
                        raise ValueError(f"invalid replanning level: {replanning_data['replanning_level']}")

   
    def _execute_task_list(
        self,
        tasks: List[TaskRecord]
    ) -> Tuple[bool, Optional[EvaluatorResult]]:
        """
        複数のタスクを実行する

        Args:
            tasks: List[TaskRecord] 実行するタスクのリスト

        Returns:
            Tuple[bool, Optional[EvaluatorResult]]: (実行結果の真偽値, 評価結果)
        """
        for task in tasks:
            is_successful, evaluate_result = self._execute_task(task)
            if not is_successful:
                return (False, evaluate_result)
        else:
            return (True, None)
        
    def process(self, instruction: str, additional_info: str):
        """
        instruction, additional_infoに従って、タスクを生成し、タスクを実行する
        
        Args:
            None
        
        Returns:
            None
        """
        # ジョブの開始
        job = self._start_job(instruction, additional_info)
        # タスクリストの生成
        tasks = self._generate_tasks(job)
        # タスクリストの実行
        is_successful, evaluate_result = self._execute_task_list(tasks)
        
        while True:
            if is_successful:
                return  # 完了
            else:
                # -- タスクリプランニングと実行 --
                # 未実行のタスクのstatusを"canceled"に変更
                for task in tasks:
                    if task.status == "pending":
                        task.status = "canceled"
                        self._db.update_task(task)
                        
                # リプランニングデータの選択
                assert evaluate_result is not None
                replanning_data = evaluate_result["replanning_data"]["1"]
                                
                # タスクリストの生成
                tasks = self._regenerate_tasks(job, replanning_data)
                # タスクリストの実行
                is_successful, evaluate_result = self._execute_task_list(tasks)
                
        
        