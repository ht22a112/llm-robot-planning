from typing import List, Union, Dict, Tuple, Optional, Literal
from datetime import datetime, timezone

from planner.llm.gen_ai import UnifiedAIRequestHandler
from planner.memory import Memory
from planner.command.command_base import Command
from planner.command.executor import CommandExecutor
from planner.command.robot_state import RobotState, StateChange
from planner.command.manager import CommandManager, RobotStateManager
from planner.database.database import DatabaseManager
from planner.database.data_type import TaskInfo, TaskRecord, CommandRecord, JobRecord, CommandExecutionResultRecord
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
    def __init__(
        self, 
        api_keys: dict, 
        commands: List[Command], 
        states: List[RobotState]
    ):
        """
        
        Args:
            api_keys: dict
            commands: List[Command]
            states: List[RobotState]
        """ 
        self._llm = UnifiedAIRequestHandler(
            api_keys=api_keys
        )
        
        self._db: DatabaseManager = DatabaseManager()
        self._memory: Memory = Memory()
        self._task_service = TaskService(self._llm, self._db)
        self._cmd_manager = CommandManager()
        self._cmd_executor = CommandExecutor(self._cmd_manager)
        self._state_manager = RobotStateManager()
        self._result_evaluator = ResultEvaluator(self._db, self._llm)
        
        #  TODO: テスト
        from planner.rag import RAG
        self._rag = RAG(self._db, self._llm)
        
        self._cmd_manager.register_commands(commands)
        self._state_manager.register_states(states)
        
    def init_helper(self):
        """テスト用初期化メソッド"""
        self._db.init_helper()
                
    def initialize(self):
        """
        システムの初期化
        """
        with log.span(name="初期化：") as span:
            span.input(f"初期化開始")
            self.init_helper()
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
            current_job_record = self._memory.add_job(
                instruction=instruction,
                additional_info=additional_info
            )
        return current_job_record
        
        
    def _generate_tasks(
        self,
        job: JobRecord,
        states: List[RobotState]
    ) -> List[TaskInfo]:
        with log.span(name="タスクの生成：") as span:
            span.input(f"指示: {job.description}")
            
            # タスクの生成
            tasks = self._task_service.generate_tasks(
                job.description, 
                states
            )
            
            # TODO: 後で消す
            logger.debug(to_json_str(tasks))
                        
            span.output("\n".join(f"タスク{i}:\n    タスクの説明: {task['description']}\n    タスクの詳細: {task['additional_info']}" for i, task in enumerate(tasks, 1)))
        return tasks
    
    
    def _regenerate_tasks(
        self, 
        job: JobRecord,
        states: List[RobotState],
        executed_tasks: List[TaskRecord],
        replanning_data: ReplanningData
    ) -> List[TaskInfo]:
        with log.span(name="タスクの生成：") as span:
            span.input(f"指示: {job.description}")
            
            # タスクの生成
            tasks = self._task_service.regenerate_tasks(
                instruction=job.description,
                states=states,
                executed_tasks=executed_tasks,
                replanning_data=replanning_data
            )
            
            span.output("\n".join(f"タスク{i}:\n    タスクの説明: {task['description']}\n    タスクの詳細: {task['additional_info']}" for i, task in enumerate(tasks, 1)))
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
                command_description_list=self._cmd_manager.get_all_command_descriptions(), 
                command_history=self._memory.get_all_actions(),
                knowledge=doc)
            

        
            span.output(f"plan: {to_json_str(commands)}")
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
                command_description_list=self._cmd_manager.get_all_command_descriptions(), 
                command_history=self._memory.get_all_actions(),
                knowledge=doc
            )
    
            span.output(f"plan: {to_json_str(commands)}")
        return commands
    
    def _execute_command(self, command: CommandRecord) -> Tuple[CommandRecord, List[StateChange]]:
        """
        引数に与えられたCommandRecordに対応するコマンドを実行して、そのコマンド実行結果を記録する
        
        Args:
            command: CommandRecord
        
        Returns:
            CommandRecord: 実行結果を含むCommandRecord
        """
        # コマンドの実行
        with self._memory.log_exec_command(command) as memory:
            cmd_result = self._cmd_executor.execute_command(command)
            memory.change_execution_result(
                new_status=cmd_result.status,
                detailed_info=cmd_result.details
            )
        return command, cmd_result.state_changes
    
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
                exec_result, state_changes = self._execute_command(cmd)
                
                # ロボットの状態の更新
                self._state_manager.update(state_changes)
                
                # コマンドの実行結果の評価および分析
                evaluate_result = self._result_evaluator.evaluate_execution_command_result(task, cmd)
                # TODO: debug用　後で消す
                self._state_manager.print_all()
                if evaluate_result["is_replanning_needed"]:
                    # リプランニングが必要（実行に失敗）
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
            with self._memory.log_exec_task(task) as exec_task:
                # タスクの実行
                # --前提条件のチェック--
                # 情報条件
                # 場所（Position）の情報
                for location in task.environmental_conditions.information.locations:
                    print(location, self._rag._retrieval_potitions(location))
                    if not self._rag._retrieval_potitions(location):
                        # 情報が不足
                        action.output("失敗")
                        raise ValueError("情報が足りません")
                    
                
                # コマンドリストの生成
                commands = self._generate_commands(task)
                # コマンドリストをメモリーに登録
                self._memory.add_execution_commands(task, commands)
                # コマンドリストの実行
                is_successful, evaluate_result = self._execute_command_list(
                    task=task, 
                    commands=self._memory.get_execution_commands()
                )
                
                while True:
                    if is_successful and evaluate_result is None:
                        # コマンドリストの実行が成功した場合
                        action.output("成功")
                        exec_task.change_execution_result("success")
                        self._memory.cleanup_execution_commands()
                        return (is_successful, evaluate_result)
                    else:
                        # コマンドリストの実行が失敗（リプランニングが必要）
                        assert evaluate_result is not None
                        
                        # リプランニングデータの選択
                        replanning_data = evaluate_result["replanning_data"]["1"]
            
                        # -- リプランニング --
                        # 未実行のコマンドのstatusを"canceled"に変更
                        self._memory.cleanup_pending_execution_commands()
                        
                        if replanning_data["replanning_level"] == "task_level":
                            # タスクレベルのリプランニング
                            action.output("失敗")
                            exec_task.change_execution_result("failure")
                            return (False, evaluate_result)
                        elif replanning_data["replanning_level"] == "command_level":
                            # コマンドレベルのリプランニング
                            commands = self.regenerate_commands(task, replanning_data)
                            # コマンドリストをメモリーに登録
                            self._memory.add_execution_commands(task, commands)
                            # コマンドリストの実行
                            is_successful, evaluate_result = self._execute_command_list(
                                task=task, 
                                commands=self._memory.get_execution_commands()
                            )
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
        
        ※additional_infoは未実装
        
        Args:
            None
        
        Returns:
            None
        """
        # ジョブの開始
        job = self._start_job(instruction, additional_info)
        # タスクリストの生成
        tasks = self._generate_tasks(job, self._state_manager.get_all())
        # タスクをメモリーに登録
        self._memory.add_execution_tasks(tasks)
        # タスクリストの実行
        is_successful, evaluate_result = self._execute_task_list(
            tasks=self._memory.get_execution_tasks()
        )
        
        while True:
            if is_successful:
                return  # 完了
            else:
                # -- タスクリプランニングと実行 --
                # 未実行のタスクのstatusを"canceled"に変更して、execution_tasksから削除
                self._memory.cleanup_pending_execution_tasks()
                        
                # リプランニングデータの選択
                assert evaluate_result is not None
                replanning_data = evaluate_result["replanning_data"]["1"]
                                
                # タスクリストの生成
                tasks = self._regenerate_tasks(
                    job=job,
                    states=self._state_manager.get_all(), 
                    executed_tasks=self._memory.get_last_executed_tasks(),
                    replanning_data=replanning_data
                )
                # タスクをメモリーに登録
                self._memory.add_execution_tasks(tasks)
                # タスクリストの実行
                is_successful, evaluate_result = self._execute_task_list(
                    tasks=self._memory.get_execution_tasks()
                )