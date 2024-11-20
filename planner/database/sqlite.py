from typing import Literal, Optional, List, Dict, Any, Union, overload
from datetime import datetime
import sqlite3
import json

from planner.database.data_type import Location, Position
from planner.database.data_type import JobRecord, TaskRecord, CommandRecord, ExecutionResultRecord, CommandExecutionResultRecord
from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

import logging
logger = logging.getLogger("SQLite")

class SQLiteInterface():
    def __init__(self, db_path: str):
        self._conn: sqlite3.Connection
        self._cursor: sqlite3.Cursor
        self._db_path = db_path
        self.connect()
        
    def connect(self):
        self._conn = sqlite3.connect(self._db_path)
        self._cursor = self._conn.cursor()
        
    def close(self):
        self._conn.close()
    

class PlanningHistory:
    def __init__(self, sqlite_interface) -> None:
        self._sqlite_interface = sqlite_interface
        self._cursor: sqlite3.Cursor = sqlite_interface._cursor
        self._conn: sqlite3.Connection = sqlite_interface._conn
        self.initialize_database()

    def initialize_database(self):
        """
        データベースを初期化し、必要なテーブルを作成します。
        注意: 本番環境では DROP TABLE を実行しないようにしてください。
        """
        # 開発中のみに使用
        self._cursor.execute('''DROP TABLE IF EXISTS Jobs''')
        self._cursor.execute('''DROP TABLE IF EXISTS Tasks''')
        self._cursor.execute('''DROP TABLE IF EXISTS Commands''')
        self._cursor.execute('''DROP TABLE IF EXISTS InstructionExecutionResults''')
        self._cursor.execute('''DROP TABLE IF EXISTS TaskExecutionResults''')
        self._cursor.execute('''DROP TABLE IF EXISTS CommandExecutionResults''')
        self._cursor.execute('''DROP TABLE IF EXISTS ReplanningEvents''')

        # 外部キー制約を有効化
        self._cursor.execute("PRAGMA foreign_keys = ON;")

        # Jobs テーブル
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS Jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tasks テーブル
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                sequence_number INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                task_name TEXT NOT NULL,
                task_details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
            )
        ''')

        # Commands テーブル
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS Commands (
                command_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                sequence_number INTEGER NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                command_description TEXT,
                command_args TEXT,  -- JSON形式で引数を保持
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES Tasks(task_id)
            )
        ''')

        # ExecutionResults テーブル（Job用）
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS InstructionExecutionResults (
                job_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL,
                detailed_info TEXT,
                start_time DATETIME,
                end_time DATETIME,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES Jobs(job_id)
            )
        ''')

        # ExecutionResults テーブル（Task用）
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS TaskExecutionResults (
                task_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL,
                detailed_info TEXT,
                start_time DATETIME,
                end_time DATETIME,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES Tasks(task_id)
            )
        ''')

        # ExecutionResults テーブル（Command用）
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS CommandExecutionResults (
                command_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL,
                detailed_info TEXT,
                x REAL,
                y REAL,
                z REAL,
                start_time DATETIME,
                end_time DATETIME,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (command_id) REFERENCES Commands(command_id)
            )
        ''')

        # ReplanningEvents テーブル
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS ReplanningEvents (
                replanning_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                trigger_task_id INTEGER,
                trigger_command_id INTEGER,
                reason TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES Jobs(job_id),
                FOREIGN KEY (trigger_task_id) REFERENCES Tasks(task_id),
                FOREIGN KEY (trigger_command_id) REFERENCES Commands(command_id)
            )
        ''')
        self._conn.commit()
        logger.info("データベースの初期化が完了しました。")

    def add_job(self, job: JobRecord) -> int:
        """
        Jobを追加する

        Args:
            job: JobRecord ジョブ情報

        Returns:
            int: 追加したJobのUID
        """
        assert job.uid == -1, "JobRecord の UID は -1（未登録を示す）である必要があります。"
        self._cursor.execute('''
            INSERT INTO Jobs (content, status, timestamp)
            VALUES (?, ?, ?)
        ''', (
            job.description,
            job.status,
            job.timestamp.isoformat()
        ))
        job_id = self._cursor.lastrowid
        self._conn.commit()
        logger.info(f"Job {job_id} を追加しました。")
        return job_id

    def add_task(self, task: TaskRecord, job_id: int) -> int:
        """
        Taskを追加する

        Args:
            task: TaskRecord タスク情報
            job_id: int タスクが属するジョブのUID

        Returns:
            int: 追加したTaskのUID
        """
        assert task.uid == -1, "TaskRecord の UID は -1（未登録を示す）である必要があります。"
        self._cursor.execute('''
            INSERT INTO Tasks (job_id, sequence_number, status, task_name, task_details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            task.sequence_number,
            task.status,
            task.description,
            task.additional_info,
            task.timestamp.isoformat()
        ))
        task_id = self._cursor.lastrowid
        self._conn.commit()
        logger.info(f"Task {task_id} を追加しました。")
        return task_id

    def add_tasks(
        self, 
        tasks: List[TaskRecord], 
        job_id: int
    ) -> List[int]:
        """
        複数のTaskを追加する

        Args:
            tasks: List[TaskRecord] タスク情報のリスト
            job_id: int タスクが属するジョブのUID

        Returns:
            List[int]: 追加したTaskのUIDのリスト
        """
        task_ids = [self.add_task(task, job_id) for task in tasks]
        logger.info(f"{len(task_ids)} 件のTaskを追加しました。")
        return task_ids

    def add_command(
        self, 
        command: CommandRecord,
        task_id: int
    ) -> int:
        """
        コマンドを追加する

        Args:
            command: CommandRecord コマンド情報
            task_id: int コマンドが属するタスクのUID

        Returns:
            int: 追加したCommandのUID
        """
        assert command.uid == -1, "CommandRecord の UID は -1（未登録を示す）である必要があります。"
        command_args_json = json.dumps(command.args) if command.args else None
        self._cursor.execute('''
            INSERT INTO Commands (task_id, sequence_number, action, status, command_description, command_args, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            command.sequence_number,
            command.description,
            command.status,
            command.additional_info,
            command_args_json,
            command.timestamp.isoformat()
        ))
        command_id = self._cursor.lastrowid
        self._conn.commit()
        logger.info(f"Command {command_id} を追加しました。")
        return command_id

    def add_commands(
        self,
        commands: List[CommandRecord],
        task_id: int
    ) -> List[int]:
        """
        複数のコマンドを追加する

        Args:
            commands: List[CommandRecord] コマンド情報のリスト
            task_id: int コマンドが属するタスクのUID

        Returns:
            List[int]: 追加したCommandのUIDのリスト
        """
        command_ids = [self.add_command(command, task_id) for command in commands]
        logger.info(f"{len(command_ids)} 件のCommandを追加しました。")
        return command_ids

    def add_execution_result(
        self, 
        execution_result: Union[ExecutionResultRecord, CommandExecutionResultRecord], 
        entity_type: Literal["instruction", "task", "command"],
        entity_id: int
    ):
        """
        実行結果を追加する

        Args:
            execution_result: ExecutionResultRecord または CommandExecutionResultRecord 実行結果
            entity_type: 'instruction', 'task', 'command'
            entity_id: 対応するID

        Returns:
            None
        """
        assert entity_type in ['instruction', 'task', 'command'], f"entity_type は 'instruction', 'task', 'command' のいずれかである必要があります。"
        assert isinstance(execution_result, ExecutionResultRecord) or isinstance(execution_result, CommandExecutionResultRecord), "execution_result は ExecutionResultRecord または CommandExecutionResultRecord のいずれかである必要があります。"
        assert execution_result.uid == -1, "ExecutionResultRecord の UID は -1（未登録を示す）である必要があります。"
        assert entity_id > 0, "entity_id は 1以上の整数である必要があります。"
        
        if entity_type == 'instruction':
            self._cursor.execute('''
                INSERT INTO InstructionExecutionResults (job_id, status, detailed_info, start_time, end_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                execution_result.status,
                execution_result.detailed_info,
                execution_result.start_time.isoformat() if execution_result.start_time else None,
                execution_result.end_time.isoformat() if execution_result.end_time else None,
                execution_result.timestamp.isoformat()
            ))
            logger.info(f"InstructionExecutionResult を Job {entity_id} に追加しました。")
        elif entity_type == 'task':
            self._cursor.execute('''
                INSERT INTO TaskExecutionResults (task_id, status, detailed_info, start_time, end_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                execution_result.status,
                execution_result.detailed_info,
                execution_result.start_time.isoformat() if execution_result.start_time else None,
                execution_result.end_time.isoformat() if execution_result.end_time else None,
                execution_result.timestamp.isoformat()
            ))
            logger.info(f"TaskExecutionResult を Task {entity_id} に追加しました。")
        elif entity_type == 'command' and isinstance(execution_result, CommandExecutionResultRecord):
            self._cursor.execute('''
                INSERT INTO CommandExecutionResults (command_id, status, detailed_info, x, y, z, start_time, end_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                execution_result.status,
                execution_result.detailed_info,
                execution_result.x,
                execution_result.y,
                execution_result.z,
                execution_result.start_time.isoformat() if execution_result.start_time else None,
                execution_result.end_time.isoformat() if execution_result.end_time else None,
                execution_result.timestamp.isoformat()
            ))
            logger.info(f"CommandExecutionResult を Command {entity_id} に追加しました。")
        
        self._conn.commit()

    def add_replanning_event(self, replanning_event: dict) -> int:
        """
        ReplanningEvent を追加する

        Args:
            replanning_event: {
                'job_id': int,
                'trigger_task_id': Optional[int],
                'trigger_command_id': Optional[int],
                'reason': str
            }

        Returns:
            int: 追加したReplanningEventのID
        """
        self._cursor.execute('''
            INSERT INTO ReplanningEvents (job_id, trigger_task_id, trigger_command_id, reason)
            VALUES (?, ?, ?, ?)
        ''', (
            replanning_event['job_id'],
            replanning_event.get('trigger_task_id'),
            replanning_event.get('trigger_command_id'),
            replanning_event['reason']
        ))
        replanning_event_id = self._cursor.lastrowid
        self._conn.commit()
        logger.info(f"ReplanningEvent {replanning_event_id} を追加しました。")
        return replanning_event_id

    # --- データ取得関数 ---
    
    def get_all_command_execution_result(self) -> List[CommandExecutionResultRecord]:
        """
        全てのCommandExecutionResultsを取得する

        Returns:
            List[CommandExecutionResultRecord]: 全てのコマンド実行結果のリスト
        """
        self._cursor.execute('''
            SELECT command_id, status, detailed_info, x, y, z, start_time, end_time, timestamp
            FROM CommandExecutionResults
        ''')
        rows = self._cursor.fetchall()
        results = [
            CommandExecutionResultRecord(
                status=row[1],
                detailed_info=row[2],
                x=row[3],
                y=row[4],
                z=row[5],
                start_time=datetime.fromisoformat(row[6]) if row[6] else None,
                end_time=datetime.fromisoformat(row[7]) if row[7] else None,
                timestamp=datetime.fromisoformat(row[8])
            ) for row in rows
        ]
        logger.info(f"{len(results)} 件のCommandExecutionResultを取得しました。")
        return results

    def get_all_commands(self) -> List[CommandRecord]:
        """
        Commands テーブルと CommandExecutionResults テーブルを結合して、
        すべてのコマンドとその実行結果を取得し、CommandRecord インスタンスのリストとして返します。

        Returns:
            List[CommandRecord]: データベース内のすべてのコマンドとその実行結果のリスト。
        """
        self._cursor.execute('''
            SELECT 
                c.command_id, 
                c.task_id, 
                c.sequence_number, 
                c.action, 
                c.status, 
                c.command_description, 
                c.command_args, 
                c.timestamp,
                cer.status AS exec_status,
                cer.detailed_info AS exec_detailed_info,
                cer.x AS exec_x,
                cer.y AS exec_y,
                cer.z AS exec_z,
                cer.start_time AS exec_start_time,
                cer.end_time AS exec_end_time,
                cer.timestamp AS exec_timestamp
            FROM Commands c
            LEFT JOIN CommandExecutionResults cer ON c.command_id = cer.command_id
            ORDER BY c.command_id ASC
        ''')
        rows = self._cursor.fetchall()

        commands = []
        for row in rows:
            (
                command_id, task_id, sequence_number, action, status, command_description, command_args, timestamp_str,
                exec_status, exec_detailed_info, exec_x, exec_y, exec_z, 
                exec_start_time_str, exec_end_time_str, exec_timestamp_str
            ) = row

            # JSON 形式の command_args を解析
            try:
                args = json.loads(command_args) if command_args else {}
            except json.JSONDecodeError as e:
                logger.error(f"command_id {command_id} の command_args のデコードに失敗しました: {e}")
                args = {}

            # タイムスタンプを datetime オブジェクトに変換
            try:
                timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
            except ValueError as e:
                logger.error(f"command_id {command_id} の timestamp の解析に失敗しました: {e}")
                timestamp = None

            # 実行結果が存在する場合は CommandExecutionResultRecord を作成
            execution_result: Optional[CommandExecutionResultRecord] = None
            if exec_status:
                try:
                    exec_start_time = datetime.fromisoformat(exec_start_time_str) if exec_start_time_str else None
                except ValueError as e:
                    logger.error(f"command_id {command_id} の exec_start_time の解析に失敗しました: {e}")
                    exec_start_time = None

                try:
                    exec_end_time = datetime.fromisoformat(exec_end_time_str) if exec_end_time_str else None
                except ValueError as e:
                    logger.error(f"command_id {command_id} の exec_end_time の解析に失敗しました: {e}")
                    exec_end_time = None

                try:
                    exec_timestamp = datetime.fromisoformat(exec_timestamp_str) if exec_timestamp_str else None
                except ValueError as e:
                    logger.error(f"command_id {command_id} の exec_timestamp の解析に失敗しました: {e}")
                    exec_timestamp = None

                execution_result = CommandExecutionResultRecord(
                    status=exec_status,
                    detailed_info=exec_detailed_info,
                    x=exec_x,
                    y=exec_y,
                    z=exec_z,
                    start_time=exec_start_time,
                    end_time=exec_end_time,
                    timestamp=exec_timestamp
                )

            command = CommandRecord(
                uid=command_id,
                status=status,
                description=action,
                sequence_number=sequence_number,
                additional_info=command_description,
                args=args,
                timestamp=timestamp,
                execution_result=execution_result
            )

            commands.append(command)

        logger.info(f"データベースから {len(commands)} 件のコマンドを取得しました。")
        return commands

    # --- 実行履歴の取得関数 ---

    def get_executed_tasks(self, job_id: int) -> List[TaskRecord]:
        """
        指定されたJobに関連する実行済みのタスクを取得する

        Args:
            job_id: int ジョブのUID

        Returns:
            List[TaskRecord]: 実行済みのタスクのリスト
        """
        self._cursor.execute('''
            SELECT task_id, sequence_number, status, task_name, task_details, timestamp
            FROM Tasks
            WHERE job_id = ? AND status IN ('success', 'failure')
            ORDER BY sequence_number
        ''', (job_id,))
        rows = self._cursor.fetchall()

        tasks = []
        for row in rows:
            task_id, seq_num, status, name, details, ts = row
            # TaskExecutionResults から詳細情報を取得
            self._cursor.execute('''
                SELECT status, detailed_info, start_time, end_time, timestamp
                FROM TaskExecutionResults
                WHERE task_id = ?
            ''', (task_id,))
            exec_row = self._cursor.fetchone()
            if exec_row:
                exec_status, exec_detailed_info, exec_start_time_str, exec_end_time_str, exec_timestamp_str = exec_row
                try:
                    exec_start_time = datetime.fromisoformat(exec_start_time_str) if exec_start_time_str else None
                    exec_end_time = datetime.fromisoformat(exec_end_time_str) if exec_end_time_str else None
                    exec_timestamp = datetime.fromisoformat(exec_timestamp_str) if exec_timestamp_str else None
                except ValueError as e:
                    logger.error(f"Task {task_id} のExecutionResult のタイムスタンプ解析に失敗しました: {e}")
                    exec_start_time = exec_end_time = exec_timestamp = None

                execution_result = ExecutionResultRecord(
                    status=exec_status,
                    detailed_info=exec_detailed_info,
                    start_time=exec_start_time,
                    end_time=exec_end_time,
                    timestamp=exec_timestamp
                )
            else:
                execution_result = None

            task = TaskRecord(
                uid=task_id,
                status=status,
                description=name,
                sequence_number=seq_num,
                additional_info=details,
                timestamp=datetime.fromisoformat(ts) if ts else None,
                execution_result=execution_result
            )
            tasks.append(task)
        logger.info(f"Job {job_id} から {len(tasks)} 件の実行済みTaskを取得しました。")
        return tasks

    def get_executed_commands(self, task_id: int) -> List[CommandRecord]:
        """
        指定されたTaskに関連する実行済みのコマンドを取得する

        Args:
            task_id: int タスクのUID

        Returns:
            List[CommandRecord]: 実行済みのコマンドのリスト
        """
        self._cursor.execute('''
            SELECT command_id, sequence_number, action, status, command_description, command_args, timestamp
            FROM Commands
            WHERE task_id = ? AND status IN ('success', 'failure')
            ORDER BY sequence_number
        ''', (task_id,))
        rows = self._cursor.fetchall()

        commands = []
        for row in rows:
            command_id, seq_num, action, status, description, args_json, ts = row
            try:
                args = json.loads(args_json) if args_json else {}
            except json.JSONDecodeError as e:
                logger.error(f"Command {command_id} の args デコードに失敗しました: {e}")
                args = {}

            try:
                timestamp = datetime.fromisoformat(ts) if ts else None
            except ValueError as e:
                logger.error(f"Command {command_id} の timestamp 解析に失敗しました: {e}")
                timestamp = None

            # CommandExecutionResults から詳細情報を取得
            self._cursor.execute('''
                SELECT status, detailed_info, x, y, z, start_time, end_time, timestamp
                FROM CommandExecutionResults
                WHERE command_id = ?
            ''', (command_id,))
            exec_row = self._cursor.fetchone()
            if exec_row:
                exec_status, exec_detailed_info, exec_x, exec_y, exec_z, exec_start_time_str, exec_end_time_str, exec_timestamp_str = exec_row
                try:
                    exec_start_time = datetime.fromisoformat(exec_start_time_str) if exec_start_time_str else None
                    exec_end_time = datetime.fromisoformat(exec_end_time_str) if exec_end_time_str else None
                    exec_timestamp = datetime.fromisoformat(exec_timestamp_str) if exec_timestamp_str else None
                except ValueError as e:
                    logger.error(f"Command {command_id} のExecutionResult のタイムスタンプ解析に失敗しました: {e}")
                    exec_start_time = exec_end_time = exec_timestamp = None

                execution_result = CommandExecutionResultRecord(
                    status=exec_status,
                    detailed_info=exec_detailed_info,
                    x=exec_x,
                    y=exec_y,
                    z=exec_z,
                    start_time=exec_start_time,
                    end_time=exec_end_time,
                    timestamp=exec_timestamp
                )
            else:
                execution_result = None

            command = CommandRecord(
                uid=command_id,
                status=status,
                description=action,
                sequence_number=seq_num,
                additional_info=description,
                args=args,
                timestamp=timestamp,
                execution_result=execution_result
            )
            commands.append(command)
        logger.info(f"Task {task_id} から {len(commands)} 件の実行済みCommandを取得しました。")
        return commands

    def get_all_executed_commands(self) -> List[CommandRecord]:
        """
        データベース内のすべての実行済みコマンドを取得する

        Returns:
            List[CommandRecord]: 実行済みのコマンドのリスト
        """
        self._cursor.execute('''
            SELECT 
                c.command_id, 
                c.task_id, 
                c.sequence_number, 
                c.action, 
                c.status, 
                c.command_description, 
                c.command_args, 
                c.timestamp,
                cer.status AS exec_status,
                cer.detailed_info AS exec_detailed_info,
                cer.x AS exec_x,
                cer.y AS exec_y,
                cer.z AS exec_z,
                cer.start_time AS exec_start_time,
                cer.end_time AS exec_end_time,
                cer.timestamp AS exec_timestamp
            FROM Commands c
            LEFT JOIN CommandExecutionResults cer ON c.command_id = cer.command_id
            WHERE c.status IN ('success', 'failure')
            ORDER BY c.command_id ASC
        ''')
        rows = self._cursor.fetchall()

        commands = []
        for row in rows:
            (
                command_id, task_id, seq_num, action, status, description, args_json, ts,
                exec_status, exec_detailed_info, exec_x, exec_y, exec_z, 
                exec_start_time_str, exec_end_time_str, exec_timestamp_str
            ) = row

            # JSON 形式の command_args を解析
            try:
                args = json.loads(args_json) if args_json else {}
            except json.JSONDecodeError as e:
                logger.error(f"Command {command_id} の args デコードに失敗しました: {e}")
                args = {}

            # タイムスタンプを datetime オブジェクトに変換
            try:
                timestamp = datetime.fromisoformat(ts) if ts else None
            except ValueError as e:
                logger.error(f"Command {command_id} の timestamp 解析に失敗しました: {e}")
                timestamp = None

            # 実行結果が存在する場合は CommandExecutionResultRecord を作成
            execution_result: Optional[CommandExecutionResultRecord] = None
            if exec_status:
                try:
                    exec_start_time = datetime.fromisoformat(exec_start_time_str) if exec_start_time_str else None
                    exec_end_time = datetime.fromisoformat(exec_end_time_str) if exec_end_time_str else None
                    exec_timestamp = datetime.fromisoformat(exec_timestamp_str) if exec_timestamp_str else None
                except ValueError as e:
                    logger.error(f"Command {command_id} の ExecutionResult のタイムスタンプ解析に失敗しました: {e}")
                    exec_start_time = exec_end_time = exec_timestamp = None

                execution_result = CommandExecutionResultRecord(
                    status=exec_status,
                    detailed_info=exec_detailed_info,
                    x=exec_x,
                    y=exec_y,
                    z=exec_z,
                    start_time=exec_start_time,
                    end_time=exec_end_time,
                    timestamp=exec_timestamp
                )

            command = CommandRecord(
                uid=command_id,
                status=status,
                description=action,
                sequence_number=seq_num,
                additional_info=description,
                args=args,
                timestamp=timestamp,
                execution_result=execution_result
            )
            commands.append(command)
        
        logger.info(f"データベースから {len(commands)} 件の実行済みCommandを取得しました。")
        return commands

    def update_command(self, command: CommandRecord):
        """
        コマンド情報を更新する

        Args:
            command: CommandRecord 更新するコマンド情報

        Returns:
            None
        """
        self._cursor.execute('''
            UPDATE Commands
            SET status = ?, command_description = ?, command_args = ?
            WHERE command_id = ?
        ''', (
            command.status,
            command.description,
            json.dumps(command.args) if command.args else None,
            command.uid
        ))
        self._conn.commit()
        logger.info(f"Command {command.uid} の情報を更新しました。")    

    def update_task(self, task: TaskRecord):
        """
        タスク情報を更新する
        
        Args:
            task: TaskRecord 更新するタスク情報
            
        Returns:
            None
        """
        self._cursor.execute('''
            UPDATE Tasks
            SET status = ?, task_name = ?, task_details = ?
            WHERE task_id = ?
        ''', (
            task.status,
            task.description,
            task.additional_info,
            task.uid
        ))
        self._conn.commit()
        logger.info(f"Task {task.uid} の情報を更新しました。")
        
# Knowledge
class Knowledge():
    pass

class ObjectKnowledge(Knowledge):
    def __init__(self, sqlite_interface: SQLiteInterface):
        self._sqlite_interface: SQLiteInterface = sqlite_interface
        self._cursor: sqlite3.Cursor = sqlite_interface._cursor
        self._conn: sqlite3.Connection = sqlite_interface._conn
    
    def _create_table(self):
        # TODO: 後で過去のデーターベースの削除や保存方法の変更
        self._cursor.execute('''DROP TABLE IF EXISTS objects''')
        self._cursor.execute('''
        CREATE TABLE IF NOT EXISTS objects (
            object_id TEXT PRIMARY KEY,
            object_type TEXT NOT NULL,
            description TEXT,
            x REAL,
            y REAL,
            z REAL,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        ''')
        
    def execute_query(self, query: str):
        try:
            self._cursor.execute(query)
            result = self._cursor.fetchall()
            return result
        except sqlite3.Error as e:
            # TODO: あとで仕様を変える
            raise e

    def insert_object(self, object_id: str, object_type: str, description: str, x: float, y: float, z: float, confidence: float, metadata: str):
        self._cursor.execute(f'''
        INSERT INTO objects (object_id, object_type, description, x, y, z, confidence, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            object_id,
            object_type,
            description,
            x,
            y,
            z,
            confidence,
            metadata
        ))
        self._conn.commit()
    
    
class LocationKnowledge(Knowledge):
    def __init__(self, sqlite_interface: SQLiteInterface):
        self._sqlite_interface: SQLiteInterface = sqlite_interface
        self._cursor: sqlite3.Cursor = sqlite_interface._cursor
        self._conn: sqlite3.Connection = sqlite_interface._conn
        self._create_table()
        
    def _create_table(self):
        """テーブルを作成（存在しない場合のみ）"""
        
        self._cursor.execute('''DROP TABLE IF EXISTS locations''')
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                location_id TEXT PRIMARY KEY,
                location_name TEXT NOT NULL,
                description TEXT,
                x REAL,
                y REAL,
                z REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
 
    def add(self, 
        location_id: str, 
        location_name: str, 
        description: str, 
        x: float, 
        y: float, 
        z: float,
        timestamp: Optional[float] = None
    ):
        """
        ロケーション情報を追加する
        
        args:
            location_id: str ロケーションのID
            location_name: str ロケーションの名前
            description: str ロケーションの説明
            x: float x座標
            y: float y座標
            z: float z座標
            timestamp: float タイムスタンプ
        """
        
        self._cursor.execute(f'''
        INSERT INTO locations (location_id, location_name, description, x, y, z, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, {timestamp if timestamp is not None else 'CURRENT_TIMESTAMP'})
        ''', (
            location_id,
            location_name,
            description,
            x,
            y,
            z
        ))
        self._conn.commit()
        
        
    def delete(self, location_id: str):
        """
        指定したlocation_idのデータを削除する
        
        args:
            location_id: str 削除するデータのlocation_id
        
        return:
            bool 削除が成功した場合はTrue、失敗した場合はFalse
        """
        
        self._cursor.execute(f'''
        DELETE FROM locations WHERE location_id = ?
        ''', (location_id,))
        self._conn.commit()
        return self._cursor.rowcount > 0
    
        
    def get(self, ):
        pass
    
    def get_all(self) -> List[Location]:
        """
        すべてのロケーション情報を取得する
        
        return:
            list: すべてのロケーション情報が含まれたリスト
        """
        with log.span(name="ロケーション情報を取得") as span:
            span.input("get_all_locations")
            
            self._cursor.execute('''
            SELECT location_id, location_name, description, x, y, z, timestamp
            FROM locations
            ''')
            rows = self._cursor.fetchall()
            
            span.output(f"successfully get {len(rows)} locations")
            return [
                Location(
                    uid=row[0],
                    name=row[1],
                    description=row[2],
                    position=Position(row[3], row[4], row[5]),
                    timestamp=row[6]
                ) for row in rows
            ]
        
    
    
    # def _create_object_table(self):
    #     """必要なテーブルを作成（存在しない場合のみ）"""
    #     self._cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS data (
    #         object_id TEXT PRIMARY KEY,
    #         object_type TEXT,
    #         description TEXT,
    #         frame TEXT,
    #         x REAL,
    #         y REAL,
    #         z REAL,
    #         confidence REAL,
    #         timestamp TEXT
    #     )
    #     ''')
    #     self.conn.commit()
    