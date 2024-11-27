from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Union, Literal, Any, Tuple, TypedDict, NamedTuple
from datetime import datetime, timezone
from utils.utils import to_json_str

class Position(NamedTuple):
    x: float
    y: float
    z: float

@dataclass
class Object():
    uid: str
    name: str
    description: Optional[float]
    position: Position
    confidence: float  # 実装予定
    timestamp: float
    metadata: Optional[str]
    
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


# --- 実行結果のデータクラス ---

@dataclass
class ExecutionResultRecord(_DataRecordBase):
    uid: int = -1  # 識別子, uid(unique id)の発行はMemoryクラスが行う
    status: Union[Literal["pending"] , Literal["success"], Literal["failure"]] = "pending"
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
@dataclass(frozen=True)
class Dependencies():
    dependency_sequence_number: int
    reason: str
    required_outcome_desired_information_uids: Tuple[str, ...] = field(default_factory=tuple)
    required_outcome_desired_robot_state_uids: Tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class InformationConditions():
    locations: Tuple[str, ...] = field(default_factory=tuple)
    objects: Tuple[str, ...] = field(default_factory=tuple)
    
@dataclass(frozen=True)
class EnvironmentalConditions():
    physical: Tuple[str, ...] = field(default_factory=tuple)
    information: InformationConditions = field(default_factory=InformationConditions)

@dataclass(frozen=True)
class DesiredInformation():
    uid: int
    description: str

@dataclass(frozen=True)
class DesiredRobotState():
    uid: int
    name: str
    args: Tuple[str, ...] = field(default_factory=tuple)
    
@dataclass(frozen=True)
class TaskOutcome():
    desired_information: Tuple[DesiredInformation, ...] = field(default_factory=tuple)
    desired_robot_state: Tuple[DesiredRobotState, ...] = field(default_factory=tuple)


# --- コマンド、タスク、ジョブのデータクラス ---
class CommandInfo(TypedDict):
    sequence_number: int
    description: str
    additional_info: str
    args: Dict[str, str]
        
@dataclass
class CommandRecord(_DataRecordBase):
    # 識別子
    # uid(unique id)の発行はMemoryクラスが行う
    uid: int  # Command unique_id
    task_uid: int  # 親となるtaskのunique_id
    
    sequence_number: int
    description: str
    additional_info: str = ""
    args: Dict[str, str] = field(default_factory=dict)
    
    _status: Union[
        Literal["pending"], 
        Literal["in_progress"], 
        Literal["success"], 
        Literal["failure"], 
        Literal["canceled"]
    ] = "pending"
    execution_result: CommandExecutionResultRecord = field(default_factory=lambda: CommandExecutionResultRecord())
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __json__(self) -> dict:
        d = super().__json__()
        d["timestamp"] = str(self.timestamp.timestamp())
        return d

    def __setattr__(self, key, value):
        # 変更可能なフィールド
        mutable_fields = {"_status"}

        # 初期化済みで、変更禁止のフィールドに代入しようとした場合エラー
        if key in self.__dict__ and key not in mutable_fields:
            raise AttributeError(f"Field '{key}' is immutable and cannot be modified.")
        
        # デフォルトの代入処理を実行
        super().__setattr__(key, value)

    @property
    def status(self) -> Literal["pending", "in_progress", "success", "failure", "canceled"]:
        return self._status
    
    def change_execution_result(self, new_status: Literal["success", "failure"], detailed_info="", x:Optional[float] = None, y:Optional[float] = None, z:Optional[float] = None):
        self.execution_result.status = new_status
        self.execution_result.detailed_info = detailed_info
        self.execution_result.x = x
        self.execution_result.y = y
        self.execution_result.z = z
        self._status = new_status
        
class TaskInfo(TypedDict):
    """
    タスクの内容に関する情報を一時的に持つクラス
    各要素は全てイミュータブルで構成されている
    """
    sequence_number: int
    description: str
    additional_info: str
    dependencies: Tuple[Dependencies, ...]
    environmental_conditions: EnvironmentalConditions
    reason: str
    outcome: TaskOutcome
    
@dataclass
class TaskRecord(_DataRecordBase):
    """
    タスクの情報を保持するデータクラス
    
    _statusのみ変更可能なフィールド（ミュータブル）※_statusの変更はchange_execution_resultメソッドを使用
    それ以外のフィールドは全てイミュータブル（ただしexecution_resultが持つExecutionResultRecordクラスの各属性は変更可能）
    """
    # 識別子
    # uid(unique id)の発行はMemoryクラスが行う
    uid: int  # task unique_id
    job_uid: int  # 親となるjobのunique_id

    # タスクの情報
    sequence_number: int
    description: str
    additional_info: str = ""
    dependencies: Tuple[Dependencies, ...] = field(default_factory=tuple)
    environmental_conditions: 'EnvironmentalConditions' = field(default_factory=lambda: EnvironmentalConditions())
    reason: str = ""
    outcome: TaskOutcome = field(default_factory=lambda: TaskOutcome())

    # タスクの実行情報
    _status: Union[
        Literal["pending"],
        Literal["in_progress"],
        Literal["success"],
        Literal["failure"],
        Literal["canceled"]
    ] = "pending"
    execution_result: ExecutionResultRecord = field(default_factory=lambda: ExecutionResultRecord())
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __setattr__(self, key, value):
        # 変更可能なフィールド
        mutable_fields = {"_status"}

        # 初期化済みで、変更禁止のフィールドに代入しようとした場合エラー
        if key in self.__dict__ and key not in mutable_fields:
            raise AttributeError(f"Field '{key}' is immutable and cannot be modified.")
        
        # デフォルトの代入処理を実行
        super().__setattr__(key, value)
    
    @property
    def status(self) -> Literal["pending", "in_progress", "success", "failure", "canceled"]:
        return self._status
    
    def change_execution_result(self, new_status: Literal["success", "failure"], detailed_info=""):
        self.execution_result.status = new_status
        self.execution_result.detailed_info = detailed_info
        self._status = new_status
        
    def __json__(self) -> dict:
        d = super().__json__()
        d["timestamp"] = str(self.timestamp.timestamp())
        return d
    
    
@dataclass
class JobRecord(_DataRecordBase):
    # 識別子
    uid: int
    
    # ジョブの情報
    description: str
    additional_info: str = ""
    
    # ジョブの実行情報
    status: Union[
        Literal["pending"], 
        Literal["in_progress"], 
        Literal["success"], 
        Literal["failure"], 
        Literal["canceled"]
    ] = "pending"
    execution_result: Optional[ExecutionResultRecord] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
        
    
__all__ = [
    "Position",
    "Object",
    "Location",
    "ExecutionResultRecord",
    "CommandRecord",
    "TaskRecord",
    "JobRecord",
    "TaskInfo",
    "CommandInfo"
]