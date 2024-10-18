from typing import Literal, Optional, List, Dict, Any
import sqlite3

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class SQLiteInterface():
    def __init__(self, db_path: str):
        self._conn: sqlite3.Connection
        self._cursor: sqlite3.Cursor
        self._db_path = db_path
        self.connect()
        self._create_robot_action_history_table()
        
    def connect(self):
        self._conn = sqlite3.connect(self._db_path)
        self._cursor = self._conn.cursor()
        
    def close(self):
        self._conn.close()
        
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
        status: Literal["succeeded", "failed"],
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

    def get_all_actions(self) -> List[Dict[str, Any]]:
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
 
    def insert(self, 
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
    
    def get_all(self) -> list:
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
                {
                    'location_id': row[0],
                    'location_name': row[1],
                    'description': row[2],
                    'x': row[3],
                    'y': row[4],
                    'z': row[5],
                    'timestamp': row[6]
                } for row in rows
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
    