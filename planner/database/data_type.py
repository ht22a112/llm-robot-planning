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
    


# Records
@dataclass
class _DataRecordBase():
    def __json__(self) -> dict:
        return self.to_dict()
    
    def to_dict(self):
        """データクラスを辞書に変換する(asdict()のラッパー)"""
        return asdict(self)
    
    def to_json_str(self, **kwarg) -> str:
        """データクラスをJSON文字列に変換する"""
        return to_json_str(self, **kwarg)

@dataclass  
class _TimeRecord(_DataRecordBase):
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __json__(self) -> dict:
        d = super().__json__()
        d["timestamp"] = self.timestamp.isoformat()
        return d
    
@dataclass
class _ContentRecord(_DataRecordBase):
    action: str
    additional_info: str
    
@dataclass
class _SequenceRecord(_DataRecordBase):
    sequence_number: int

@dataclass
class ExecutionResultRecord(_TimeRecord, _DataRecordBase):
    result: str = ""
    error_message: Optional[str] = None
    detailed_info: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
@dataclass
class CommandRecord(_TimeRecord, _ContentRecord, _SequenceRecord):
    uid: Optional[int] = None  # DBからの自動生成ID
    status: Union[Literal["pending"], Literal["success"], Literal["failure"]] = "pending"
    is_active: bool = True
    execution_result: Optional[ExecutionResultRecord] = None
    args: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class TaskRecord(_TimeRecord, _ContentRecord, _SequenceRecord):
    uid: Optional[int] = None  # DBからの自動生成ID
    status: Union[Literal["pending"], Literal["success"], Literal["failure"]] = "pending"
    is_active: bool = True
    execution_result: Optional[ExecutionResultRecord] = None  # Taskの実行結果
    commands: List[CommandRecord] = field(default_factory=list)
    
@dataclass
class JobRecord(_TimeRecord, _ContentRecord):
    uid: Optional[int] = None  # DBからの自動生成ID
    status: Union[Literal["pending"], Literal["success"], Literal["failure"]] = "pending"
    is_active: bool = True
    execution_result: Optional[ExecutionResultRecord] = None  # Instructionの実行結果
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