from dataclasses import dataclass

@dataclass(frozen=True)
class Position():
    x: float
    y: float
    z: float

@dataclass
class Object():
    obj_id: str
    name: str
    description: str
    position: Position
    
@dataclass
class Location():
    """ロケーション情報
    
    Attributes:
        uid: str ロケーションのID
        name: str ロケーションの名前
        description: str ロケーションの説明
        position: Position ロケーションの座標
        timestamp: float 情報を記録したときのタイムスタンプ
    """

    uid: str
    name: str
    description: str
    position: Position
    timestamp: float
    


# Record
class CommandRecord():
    def __init__(
        self,
        name,
        details,
        status,
        position,
        timestamp,
    ):
        self.name = name
        self.details = details
        self.status = status
        self.postion = position
        self.timestamp = timestamp
    
    
class TaskRecord():
    def __init__(
        self, 
        description: str,
        detail: str,
        required_info: list[str] = [],
    ):
        self.description: str = description
        self.detail: str = detail
        self.required_info = required_info
        self.status = None
        self.commands = {}
        
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
        tasks: list[TaskRecord]
    ):
        self.instruction: str = instruction
        self.tasks: list[TaskRecord] = tasks