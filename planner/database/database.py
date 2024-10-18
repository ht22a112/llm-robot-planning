from typing import Optional, List, Literal

class Task():
    def __init__(
        self, 
        description: str,
        detail: str,
        required_info: list[str] = [],
    ):
        self.description: str = description
        self.detail: str = detail
        self.required_info = required_info
        self.commands = {}
        #self.done = False
        
    def __str__(self):
        return f"[description:{self.description}, required_info:{self.required_info}]"
    def __repr__(self):
        return self.__str__()
    
    def to_dict(self):
        return {
            "description": self.description,
            "detail": self.detail,
            "required_info": self.required_info
        }
        
class JobRecord():
    def __init__(
        self,
        instruction: str,
        tasks: list[Task]
    ):
        self.instruction: str = instruction
        self.tasks: list[Task] = tasks


class Database():
    def __init__(self):
        self.records = {}
        self.current_job: Optional[JobRecord] = None

from planner.database.sqlite import SQLiteInterface

class DatabaseManager():
    def __init__(self):
        db_path = "planner/database/db/test.db"
        self._memory_db = Database()
        self._sql_db = SQLiteInterface(db_path)
        
    def start_new_job(self, instruction: str, tasks: list[Task]):
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        Returns:
            None
        """
        self._memory_db.current_job = JobRecord(
            instruction=instruction,
            tasks=tasks
        )
        
    def get_current_job(self) -> JobRecord | None:
        return self._memory_db.current_job

    def log_robot_action(
        self,
        action: str,
        status: Literal["succeeded", "failed"],
        details: Optional[str],
        x: Optional[float],
        y: Optional[float],
        z: Optional[float],
        timestamp: Optional[float] = None
    ):
        self._sql_db.log_robot_action(
            action=action,
            status=status,
            details=details,
            x=x,
            y=y,
            z=z,
            timestamp=timestamp
        )
        
        
        