from typing import Optional

class Task():
    def __init__(
        self, 
        description: str,
        required_info: list[str] = [],
    ):
        self.description: str = description
        self.required_info = required_info
        self.func_dict = {}
        #self.done = False
        
    def __str__(self):
        return f"[description:{self.description}, required_info:{self.required_info}]"
    def __repr__(self):
        return self.__str__()
        
class Record():
    def __init__(
        self,
        instruction: str,
        tasks: list[Task]
    ):
        self.instruction: str = instruction
        self.tasks: list[Task] = tasks



class DatabaseManager():
    def __init__(self):
        self.data = {}
        self.current_job: Optional[Record] = None
        
    def start_new_job(self, instruction: str, tasks: list[Task]):
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        Returns:
            None
        """
        self.current_job = Record(
            instruction=instruction,
            tasks=tasks
        )
        
        
        
        
        
        
        
        