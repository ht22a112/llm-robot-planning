from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Union, Literal, Any
from datetime import datetime, timezone
from utils.utils import to_json_str

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
    

# --- ベースクラスの定義 ---

@dataclass
class _DataRecordBase:
    def __json__(self) -> dict:
        return self.to_dict()
    
    def to_dict(self):
        """データクラスを辞書に変換する(asdict()のラッパー)"""
        return asdict(self)
    
    def to_json_str(self, **kwargs) -> str:
        """データクラスをJSON文字列に変換する"""
        return to_json_str(self, **kwargs)

@dataclass
class _TimeRecord(_DataRecordBase):
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __json__(self) -> dict:
        d = super().__json__()
        d["timestamp"] = self.timestamp.isoformat()
        return d

@dataclass
class _ContentRecord(_DataRecordBase):
    description: str
    additional_info: str = ""

@dataclass
class _SequenceRecord(_DataRecordBase):
    sequence_number: int

# --- 実行結果のデータクラス ---

@dataclass
class ExecutionResultRecord(_TimeRecord):
    uid: int = -1  # DBからの自動生成ID, -1は未登録を表す
    status: Union[Literal["success"], Literal["failure"]] = "success"
    detailed_info: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def __json__(self) -> dict:
        d = super().__json__()
        d["start_time"] = self.start_time.isoformat() if self.start_time else None
        d["end_time"] = self.end_time.isoformat() if self.end_time else None
        return d

@dataclass
class CommandExecutionResultRecord(ExecutionResultRecord):
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

#

@dataclass
class TaskDependencies():
    dependency_sequence_number: int
    reason: str
    required_outcome_desired_information_uids: list = field(default_factory=list)
    required_outcome_desired_robot_state_uids: list = field(default_factory=list)

@dataclass
class TaskEnvironmentalConditions():
    required_physical_conditions: list = field(default_factory=list)
    required_information_conditions: list = field(default_factory=list)

@dataclass
class TaskOutcome():
    desired_information: list = field(default_factory=list)
    desired_robot_state: list = field(default_factory=list)

@dataclass
class DesiredInformation():
    uid: int
    description: str

@dataclass
class DesiredRobotState():
    uid: int
    state_name: str
    arg: List[Any] = field(default_factory=list)

# --- コマンド、タスク、ジョブのデータクラス ---

@dataclass
class CommandRecord(_TimeRecord, _ContentRecord, _SequenceRecord):
    uid: int = -1  # DBからの自動生成ID, -1は未登録を表す
    status: Union[
        Literal["pending"], 
        Literal["in_progress"], 
        Literal["success"], 
        Literal["failure"], 
        Literal["canceled"]
    ] = "pending"
    execution_result: Optional[CommandExecutionResultRecord] = None
    args: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class TaskRecord(_TimeRecord, _ContentRecord, _SequenceRecord):
    uid: int = -1  # DBからの自動生成ID, -1は未登録を表す
    status: Union[
        Literal["pending"], 
        Literal["in_progress"], 
        Literal["success"], 
        Literal["failure"], 
        Literal["canceled"]
    ] = "pending"
    
    #
    dependencies: List[TaskDependencies] = field(default_factory=list)
    environmental_conditions: TaskEnvironmentalConditions = field(default_factory=TaskEnvironmentalConditions)
    reason: str = ""
    outcome: TaskOutcome = field(default_factory=TaskOutcome)
    
    execution_result: Optional[ExecutionResultRecord] = None  # Taskの実行結果
    commands: List[CommandRecord] = field(default_factory=list)

@dataclass
class JobRecord(_TimeRecord, _ContentRecord):
    uid: int = -1  # DBからの自動生成ID, -1は未登録を表す
    status: Union[
        Literal["pending"], 
        Literal["in_progress"], 
        Literal["success"], 
        Literal["failure"], 
        Literal["canceled"]
    ] = "pending"
    execution_result: Optional[ExecutionResultRecord] = None  # Jobの実行結果
    tasks: List[TaskRecord] = field(default_factory=list)
    
    
__all__ = [
    "Position",
    "Object",
    "Location",
    "ExecutionResultRecord",
    "CommandRecord",
    "TaskRecord",
    "JobRecord",
]