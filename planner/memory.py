from planner.database.data_type import *
from typing import Dict, Optional, List
from datetime import datetime, timezone
from contextlib import contextmanager
UniqueID = int
    
class Memory():
    """現在実行中のJob, Tasks, Commandsの情報を保持するクラス"""
    def __init__(self):
        # ジョブ
        self._job: Optional[JobRecord] = None
        # タスク
        self._tasks: Dict[UniqueID, TaskRecord]= {}  # すべてのタスク
        self._exec_tasks_view: List[TaskRecord] = []  # 実行中(または実行するべき）のタスクリストのビュー（self._tasksの値を直接参照する）
        self._last_exec_tasks_view: List[TaskRecord] = []  #  最後に実行したタスクのリストのビュー（self._tasksの値を直接参照する）
        # コマンド
        self._commands: Dict[UniqueID, CommandRecord] = {}  # すべてのコマンド
        self._exec_commands_view: List[CommandRecord] = []  # 実行中(または実行するべき）のコマンドリストのビュー（self._commandsの値を直接参照する）
        self._last_exec_commands_view: List[CommandRecord] = []  # 最後に実行したコマンドのリストのビュー（self._commandsの値を直接参照する）
        
        # ユニークID生成用
        self._count_job: UniqueID = 0
        self._count_task: UniqueID = 0
        self._count_command: UniqueID = 0
    
    
    @contextmanager
    def log_exec_task(self, task: TaskRecord):
        """
        タスクの開始時刻、終了時刻、成功/失敗、実行結果、ステータス、追加情報をRecordに記録してそのままMemoryに更新した上で保存するコンテキストマネージャ
        """
        start_time = datetime.now(timezone.utc)  # タスクの開始時刻を記録
        task._status = "in_progress"  # ステータスを更新
        
        try:
            yield task  # タスクの処理を呼び出し元に渡す
            
            if task.status == task.execution_result.status and not task.status in ("success", "failure"):
                raise ValueError(f"Task {task.uid} is already completed. task.status must be 'success' or 'failure'. status: {task.status}.")
        finally:
            end_time = datetime.now(timezone.utc)  # タスクの終了時刻を記録
            task.execution_result.start_time = start_time  # 開始時刻を更新
            task.execution_result.end_time = end_time  # 終了時刻を更新
            self.update_task(task)
    
    @contextmanager
    def log_exec_command(self, command: CommandRecord):
        """
        コマンドの開始時刻、終了時刻、成功/失敗、実行結果、ステータス、追加情報をRecordに記録してそのままMemoryに更新した上で保存するコンテキストマネージャ
        """
        start_time = datetime.now(timezone.utc)  # コマンドの開始時刻を記録
        command._status = "in_progress"  # ステータスを更新
        
        try:
            yield command  # コマンドの処理を呼び出し元に渡す
            
            if command.status == command.execution_result.status and not command.status in ("success", "failure"):
                raise ValueError(f"Command {command.uid} is already completed. command.status must be 'success' or 'failure'. status: {command.status}.")
        finally:
            end_time = datetime.now(timezone.utc)  # コマンドの終了時刻を記録
            command.execution_result.start_time = start_time  # コマンドの開始時刻を更新
            command.execution_result.end_time = end_time  # コマンドの終了時刻を更新
            self.update_command(command)
            
    def update_task(self, task: TaskRecord):
        t = self._tasks[task.uid]
        t._status = task.status
        t.execution_result.start_time = task.execution_result.start_time
        t.execution_result.end_time = task.execution_result.end_time
        t.execution_result.detailed_info = task.execution_result.detailed_info
        t.execution_result.status = task.execution_result.status
    
    def update_command(self, command: CommandRecord):
        c = self._commands[command.uid]
        c._status = command.status
        c.execution_result.start_time = command.execution_result.start_time
        c.execution_result.end_time = command.execution_result.end_time
        c.execution_result.x = command.execution_result.x
        c.execution_result.y = command.execution_result.y
        c.execution_result.z = command.execution_result.z
        
    def add_job(self, instruction, additional_info):
        self._job = JobRecord(
            uid=self._generate_job_uid(),
            description=instruction,
            additional_info=additional_info
        )
        return self._job  # TODO: コピーを返すように変更する
        
    def add_execution_task(self, task_info: TaskInfo) -> None:
        if self._job is None:
            raise ValueError("Job must be created before adding a task.")
        
        task_uid = self._generate_task_uid()
        task = self._create_task(self._job.uid, task_uid, task_info)
        
        self._tasks[task_uid] = task
        self._exec_tasks_view.append(task)
    
    def add_execution_tasks(self, task_info_list: List[TaskInfo]) -> None:
        # TODO: 処理の高速化
        for task in task_info_list:
            self.add_execution_task(task)

    def add_execution_command(self, task: TaskRecord, command_info: CommandInfo) -> None:
        if task not in self._exec_tasks_view:
            raise ValueError(f"Task {task.uid} must be executed before adding a command.")
        
        command_uid = self._generate_command_uid()
        command = self._create_command(task.uid, command_uid, command_info)
        
        self._commands[command_uid] = command
        self._exec_commands_view.append(command)
    
    def add_execution_commands(self, task: TaskRecord, command_info_list: List[CommandInfo]) -> None:
        # TODO: 処理の高速化
        for command_info in command_info_list:
            self.add_execution_command(task, command_info)
    
    def get_execution_tasks(self):
        return self._exec_tasks_view  # TODO: コピーを返すように変更する
    def get_last_executed_tasks(self):
        return self._last_exec_tasks_view   # TODO: コピーを返すように変更する
    
    def get_execution_commands(self):
        return self._exec_commands_view  # TODO: コピーを返すように変更する
    def get_last_executed_commands(self):
        return self._last_exec_commands_view  # TODO: コピーを返すように変更する
    
    def get_all_actions(self) -> List[CommandRecord]:
        # for task in self._exec_tasks_view:
        #     if task.status in ("success", "failure"):
        #         pass
        
        l = []
        for cmd in self._commands.values():
            if cmd.status in ("success", "failure"):
                l.append(cmd)
        return l    
        
    def cleanup_pending_execution_tasks(self):
        """
        1. 未実行のタスクのstatusを"canceled"にする
        2. そしてその要素を_exec_tasks_viewから削除する
        3. last_executed_tasksを更新する
        """
        
        # last_executed_tasksを更新
        self._last_exec_tasks_view = self._exec_tasks_view.copy()
        
        # TODO: タスクn番目がpendingであればタスクn+1以降はすべてpendingであることを保証する仕様にすればより効率の良いコードに変えれる
        new_index = 0  # 新しいリストのインデックス
        for i in range(len(self._exec_tasks_view)):  # 元のリストをインデックスで走査
            task = self._exec_tasks_view[i]
            if task.status == "pending":
                task._status = "canceled"  # 状態を変更
            else:
                self._exec_tasks_view[new_index] = task  # 残すべきタスクを前方に移動
                new_index += 1

        # リストを縮小
        del self._exec_tasks_view[new_index:]
    
    def cleanup_pending_execution_commands(self):
        """
        1. 未実行のコマンドのstatusを"canceled"にする
        2. そしてその要素を_exec_commands_viewから削除する
        3. last_executed_commandsを更新する
        """
        
        # last_executed_commandsを更新
        self._last_exec_commands_view = self._exec_commands_view.copy()
        
        # TODO: コマンドn番目がpendingであればコマンドn+1以降はすべてpendingであることを保証する仕様にすればより効率の良いコードに変えれる
        new_index = 0  # 新しいリストのインデックス
        for i in range(len(self._exec_commands_view)):  # 元のリストをインデックスで走査
            command = self._exec_commands_view[i]
            if command.status == "pending":
                command._status = "canceled"  # 状態を変更
            else:
                self._exec_commands_view[new_index] = command  # 残すべきコマンドを前方に移動
                new_index += 1

        # リストを縮小
        del self._exec_commands_view[new_index:]
    
    def cleanup_execution_commands(self):
        self._exec_commands_view = []
        
    def _create_task(self, job_uid: UniqueID, task_uid: UniqueID, task_info: TaskInfo) -> TaskRecord:
        """TaskRecordを生成する"""
        return TaskRecord(
            uid=task_uid,
            job_uid=job_uid,
            sequence_number=task_info["sequence_number"],
            description=task_info["description"],
            additional_info=task_info["additional_info"],
            dependencies=task_info["dependencies"],
            environmental_conditions=task_info["environmental_conditions"],
            reason=task_info["reason"],
            outcome=task_info["outcome"],
        )
        
    def _create_command(self, task_uid: UniqueID, command_uid: UniqueID, command_info: CommandInfo) -> CommandRecord:
        """CommandRecordを生成する"""
        return CommandRecord(
            uid=command_uid,
            task_uid=task_uid,
            sequence_number=command_info["sequence_number"],
            description=command_info["description"],
            additional_info=command_info["additional_info"],
            args=command_info["args"],
        )
        
    def _generate_job_uid(self):
        self._count_job += 1
        return self._count_job
    def _generate_task_uid(self):
        self._count_task += 1
        return self._count_task
    def _generate_command_uid(self):
        self._count_command += 1
        return self._count_command