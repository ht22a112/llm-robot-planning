from typing import Literal, Optional, List, Dict, Any
import sqlite3
import json

from planner.database.data_type import Location, Position
from planner.database.data_type import JobRecord, TaskRecord, CommandRecord, ExecutionResultRecord
from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

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
    

class PlanHistory():
    def __init__(self, sqlite_interface) -> None:
        self._sqlite_interface: SQLiteInterface = sqlite_interface
        self._cursor: sqlite3.Cursor = sqlite_interface._cursor
        self._conn: sqlite3.Connection = sqlite_interface._conn
        self.initialize_database()
                
    def initialize_database(self):
        # 外部キー制約を有効化
        self._cursor.execute("PRAGMA foreign_keys = ON;")
        
        # TODO: あとで変更
        self._cursor.execute('''DROP TABLE IF EXISTS Jobs''')
        self._cursor.execute('''DROP TABLE IF EXISTS Tasks''')
        self._cursor.execute('''DROP TABLE IF EXISTS Commands''')
        self._cursor.execute('''DROP TABLE IF EXISTS InstructionExecutionResults''')
        self._cursor.execute('''DROP TABLE IF EXISTS TaskExecutionResults''')
        self._cursor.execute('''DROP TABLE IF EXISTS CommandExecutionResults''')
        self._cursor.execute('''DROP TABLE IF EXISTS ReplanningEvents''')
    
        # Jobs テーブル
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS Jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                is_active BOOLEAN NOT NULL DEFAULT 1,
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
                is_active BOOLEAN NOT NULL DEFAULT 1,
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
                is_active BOOLEAN NOT NULL DEFAULT 1,
                command_description TEXT,
                command_args TEXT,  -- JSON形式で引数を保持
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES Tasks(task_id)
            )
        ''')
        
        # ExecutionResults テーブル（Instruction用）
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS InstructionExecutionResults (
                job_id INTEGER PRIMARY KEY,
                result TEXT NOT NULL,
                error_message TEXT,
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
                result TEXT NOT NULL,
                error_message TEXT,
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
                result TEXT NOT NULL,
                error_message TEXT,
                detailed_info TEXT,
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

    def add_job(self, job: JobRecord) -> int:
        """
        Jobを追加する
        
        Args:
            job: JobRecord ジョブ情報
            
        Returns:
            int: 追加したJobのUID
        """
        
        self._cursor.execute('''
            INSERT INTO Jobs (content, status, is_active, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            job.action,
            job.status,
            job.is_active,
            job.timestamp.isoformat()
        ))
        job_id = self._cursor.lastrowid
        self._conn.commit()
        return job_id

    def add_task(self, task: TaskRecord, job_id: int) -> int:
        """
        Taskを追加する
        
        Args:
            task: TaskRecord タスク情報
            job_id: int タスクが属するジョブのUID
        
        Returns:
            task_id: int 追加したTaskのUID
        """
        
        self._cursor.execute('''
            INSERT INTO Tasks (job_id, sequence_number, status, is_active, task_name, task_details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            task.sequence_number,
            task.status,
            task.is_active,
            task.action,
            task.additional_info,
            task.timestamp.isoformat()
        ))
        task_id = self._cursor.lastrowid
        self._conn.commit()
        return task_id

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
            command_id: int 追加したCommandのUID
        """
        command_args_json = json.dumps(command.args) if command.args else None
        self._cursor.execute('''
            INSERT INTO Commands (task_id, sequence_number, action, status, is_active, command_description, command_args, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            command.sequence_number,
            command.action,
            command.status,
            command.is_active,
            command.additional_info,
            command_args_json,
            command.timestamp.isoformat()
        ))
        command_id = self._cursor.lastrowid
        self._conn.commit()
        return command_id

    def add_execution_result(
        self, 
        execution_result: ExecutionResultRecord, 
        entity_type: str, 
        entity_id: int
    ):
        """
        Args:
            execution_result: ExecutionResultRecord 実行結果
            entity_type: 'instruction', 'task', 'command'
            entity_id: 対応するID
        
        Return:
            None
        """
        if entity_type == 'instruction':
            self._cursor.execute('''
                INSERT INTO InstructionExecutionResults (job_id, result, error_message, detailed_info, start_time, end_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                execution_result.result,
                execution_result.error_message,
                execution_result.detailed_info,
                execution_result.start_time.isoformat() if execution_result.start_time else None,
                execution_result.end_time.isoformat() if execution_result.end_time else None,
                execution_result.timestamp.isoformat()
            ))
        elif entity_type == 'task':
            self._cursor.execute('''
                INSERT INTO TaskExecutionResults (task_id, result, error_message, detailed_info, start_time, end_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                execution_result.result,
                execution_result.error_message,
                execution_result.detailed_info,
                execution_result.start_time.isoformat() if execution_result.start_time else None,
                execution_result.end_time.isoformat() if execution_result.end_time else None,
                execution_result.timestamp.isoformat()
            ))
        elif entity_type == 'command':
            self._cursor.execute('''
                INSERT INTO CommandExecutionResults (command_id, result, error_message, detailed_info, start_time, end_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id,
                execution_result.result,
                execution_result.error_message,
                execution_result.detailed_info,
                execution_result.start_time.isoformat() if execution_result.start_time else None,
                execution_result.end_time.isoformat() if execution_result.end_time else None,
                execution_result.timestamp.isoformat()
            ))
        else:
            raise ValueError("Invalid entity_type. Must be 'instruction', 'task', or 'command'.")
        
        self._conn.commit()
        

    def add_replanning_event(self, replanning_event: dict) -> int:
        """
        replanning_event: {
            'job_id': int,
            'trigger_task_id': Optional[int],
            'trigger_command_id': Optional[int],
            'reason': str
        }
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
        return replanning_event_id
    
    
class ActionHistory():
    def __init__(self, sqlite_interface: SQLiteInterface):
        self._sqlite_interface: SQLiteInterface = sqlite_interface
        self._cursor: sqlite3.Cursor = sqlite_interface._cursor
        self._conn: sqlite3.Connection = sqlite_interface._conn
        self._create_robot_action_history_table()
        
    def _create_robot_action_history_table(self):
        # TODO: 後で過去のデーターベースの削除や保存方法の変更
        self._cursor.execute('''DROP TABLE IF EXISTS actions''')
        self._cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            x REAL,
            y REAL,
            z REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
    def log_robot_action(self,
        action: str,
        status: Literal["success", "failure"],
        details: Optional[str],
        x: Optional[float],
        y: Optional[float],
        z: Optional[float],
        timestamp: Optional[float] = None,    
    ):      
        """
        ロボットの行動を記録

        args:
            action: str ロボットの行動
            status: str 行動のステータス
            details: str 行動の詳細
            x: float x座標
            y: float y座標
            z: float z座標
            timestamp: float タイムスタンプ        
        """

        self._cursor.execute(f'''
        INSERT INTO actions (action, status, details, x, y, z, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, {timestamp if timestamp is not None else 'CURRENT_TIMESTAMP'})
        ''', (
            action,
            status,
            details,
            x,
            y,
            z
        ))
        self._conn.commit()

    def get_all(self) -> List[Dict[str, Any]]:
        """すべての行動履歴を取得する。"""
        with log.span(name="ロボットの行動履歴を取得") as span:
            span.input("get_all_action_history") 
            self._cursor.execute('''
            SELECT id, action, status, details, x, y, z, timestamp
            FROM actions
            ORDER BY timestamp ASC
            ''')
            rows = self._cursor.fetchall()

            actions = []
            for row in rows:
                action = {
                    "id": row[0],
                    "action": row[1],
                    "status": row[2],
                    "details": row[3],
                    "position": {
                        "x": row[4],
                        "y": row[5],
                        "z": row[6]
                    } if row[4] is not None and row[5] is not None and row[6] is not None else None,
                    "timestamp": row[7]
                }
                actions.append(action)
            span.output(f"successfully get {len(actions)} actions")
        return actions



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
    