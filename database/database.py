from typing import Optional, List

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
        
class DatabaseManager():
    def __init__(self):
        self._db = Database()
        
        
    def start_new_job(self, instruction: str, tasks: list[Task]):
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        Returns:
            None
        """
        self._db.current_job = JobRecord(
            instruction=instruction,
            tasks=tasks
        )
        
    def get_current_job(self) -> JobRecord | None:
        return self._db.current_job

        
        
        
        