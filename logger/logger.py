from dataclasses import dataclass, field, asdict, replace
from typing import Dict, Any, Optional, Union, List, TypeVar, Mapping, Tuple, Set, FrozenSet
from abc import ABC, abstractmethod
from types import MappingProxyType
from contextlib import contextmanager
from enum import Enum
from uuid import uuid4
from datetime import datetime

from logger.exceptions import *

uuidv4_str = str
FeedBackValueType = Union[str, int, float, bytes, bool]
MetadataValueType = Union[str, int, float, bytes, bool]

class LogType(Enum):
    TRACE = "trace"
    ACTION = "action"
    SPAN = "span"
    EVENT = "event"

T = TypeVar('T', bound='LogRecord')

@dataclass(frozen=True)
class LogRecord(ABC):
    name: str
    tag: Union[Set[str], FrozenSet[str]] = field(default_factory=frozenset)
    metadata: Union[Dict[str, MetadataValueType], MappingProxyType[str, MetadataValueType]] = field(default_factory=lambda: MappingProxyType({}))
    parent: Optional[uuidv4_str] = field(default=None)
    children: Tuple[uuidv4_str, ...] = field(default_factory=tuple)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    uid: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        #self._validate_types()  # TODO: あとでコメントアウトを解除
        object.__setattr__(self, 'tag', frozenset(self.tag))
        object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))

    def _validate_types(self):
        if not isinstance(self.name, str):
            raise InvalidTypeError(f"name must be a string, not {type(self.name)}")
        if not isinstance(self.tag, (set, frozenset)):
            raise InvalidTypeError(f"tag must be a set or frozenset, not {type(self.tag)}")
        if not all(isinstance(t, str) for t in self.tag):
            raise InvalidTypeError("All elements in tag must be strings")  
        if not isinstance(self.metadata, Mapping):
            raise InvalidTypeError(f"metadata must be a Mapping, not {type(self.metadata)}") 
        if not isinstance(self.children, tuple):
            raise InvalidTypeError(f"children must be a tuple, not {type(self.children)}") 
        if not isinstance(self.timestamp, float):
            raise InvalidTypeError(f"timestamp must be a float, not {type(self.timestamp)}")
        if not isinstance(self.uid, str):
            raise InvalidTypeError(f"uid must be a string, not {type(self.uid)}")
        # メタデータの中身のチェック
        for k, v in self.metadata.items():
            if not isinstance(k, str):
                raise InvalidTypeError(f"All keys in metadata must be strings, found {type(k)}")
            if not isinstance(v, (str, int, float, bool)) and v is not None:
                raise InvalidTypeError(f"Invalid type {type(v)} for metadata value. Allowed types are str, int, float, bool, None")

    @property
    @abstractmethod
    def type(self) -> LogType:
        pass

    def with_child(self, child: uuidv4_str) -> 'LogRecord':
        if not isinstance(child, str):
            raise InvalidTypeError(f"child must be a string (UUID), not {type(child)}")
        return self.create_new(children=self.children + (child,))
    
    def with_tag(self, new_tag: str) -> 'LogRecord':
        if not isinstance(new_tag, str):
            raise InvalidTypeError(f"Tag must be a string, not {type(new_tag)}")
        return self.create_new(tag=self.tag | {new_tag})
    
    def with_metadata(self, key: str, value: MetadataValueType) -> 'LogRecord':
        if not isinstance(key, str):
            raise InvalidTypeError(f"Metadata key must be a string, not {type(key)}")
        if not isinstance(value, (str, int, float, bool)) and value is not None:
            raise InvalidTypeError(f"Invalid type {type(value)} for metadata value. Allowed types are str, int, float, bool, None")
        new_metadata = dict(self.metadata)
        new_metadata[key] = value
        return self.create_new(metadata=new_metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: (dict(v) if isinstance(v, MappingProxyType) else 
                    (list(v) if isinstance(v, frozenset) else v))
                for k, v in asdict(self).items()}
            
    def create_new(self: T, **changes) -> T:
        return replace(self, **changes)


@dataclass(frozen=True)
class DurationLogRecord(LogRecord):
    input: str = field(default_factory=str)
    output: str = field(default_factory=str)
    feedback: str = field(default_factory=str)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        #self._validate_types()  # TODO: あとでコメントアウトを解除

    def _validate_types(self):
        if not isinstance(self.input, str):
            raise InvalidTypeError(f"input must be a string, not {type(self.input)}")
        if not isinstance(self.output, str):
            raise InvalidTypeError(f"output must be a string, not {type(self.output)}")
        if not isinstance(self.feedback, str):
            raise InvalidTypeError(f"feedback must be a string, not {type(self.feedback)}")
        if not isinstance(self.start_time, datetime):
            raise InvalidTypeError(f"start_time must be a datetime, not {type(self.start_time)}")
        if self.end_time is not None and not isinstance(self.end_time, datetime):
            raise InvalidTypeError(f"end_time must be None or a datetime, not {type(self.end_time)}")

    @property
    def duration(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def with_end_time(self, end_time: Optional[datetime] = None) -> 'DurationLogRecord':
        """End timeを設定する関数"""
        if end_time is None:
            end_time = datetime.now()
        elif not isinstance(end_time, datetime):
            raise ValueError("end_time must be datetime")
        return self.create_new(end_time=end_time)
        
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"duration": self.duration})
        return d

@dataclass(frozen=True)
class InstantLogRecord(LogRecord):
    context: str = field(default_factory=str)

    def __post_init__(self):
        super().__post_init__()
        self._validate_types()

    def _validate_types(self):
        super()._validate_types()
        if not isinstance(self.context, str):
            raise InvalidTypeError(f"context must be a string, not {type(self.context)}")

class LogEventType(Enum):
    BEGIN = "begin"
    UPDATE = "update"
    END = "end"
    
@dataclass(frozen=True)
class LogEvent:
    event_type: LogEventType
    record: LogRecord
    previous_record: Optional[LogRecord] = None
    changes: Optional[Union[Dict[str, Any], MappingProxyType]] = field(default=None)

    def __post_init__(self):
        if self.changes is not None and not isinstance(self.changes, MappingProxyType):
            object.__setattr__(self, 'changes', MappingProxyType(dict(self.changes)))
    
@dataclass(frozen=True)
class Trace(DurationLogRecord):
    @property
    def type(self) -> LogType:
        return LogType.TRACE
    
@dataclass(frozen=True)
class Action(DurationLogRecord):
    @property
    def type(self) -> LogType:
        return LogType.ACTION

@dataclass(frozen=True)
class Span(DurationLogRecord):
    @property
    def type(self) -> LogType:
        return LogType.SPAN

@dataclass(frozen=True)
class Event(InstantLogRecord):
    @property
    def type(self) -> LogType:
        return LogType.EVENT


class LogEntryContext():
    def __init__(self, log_system: 'LLMRobotPlannerLogSystem', 
                 uid: str, log_type: LogType):
        self._log_system: LLMRobotPlannerLogSystem = log_system
        self._uid: str = uid
        self._log_type: LogType = log_type

    @property
    def uid(self) -> str:
        return self._uid
    
    def input(self, input: str):
        if self._log_type in [LogType.TRACE, LogType.ACTION, LogType.SPAN]:
            self._update(input=input)
        else:
            raise InvalidLogOperationError("input", self._log_type.value)

    def output(self, output: str):
        if self._log_type in [LogType.TRACE, LogType.ACTION, LogType.SPAN]:
            self._update(output=output)
        else:
            raise InvalidLogOperationError("output", self._log_type.value)

    def feedback(self, feedback: str):
        if self._log_type in [LogType.TRACE, LogType.ACTION, LogType.SPAN]:
            self._update(feedback=feedback)
        else:
            raise InvalidLogOperationError("feedback", self._log_type.value)

    def context(self, context: str):
        if self._log_type == LogType.EVENT:
            self._update(context=context)
        else:
            raise InvalidLogOperationError("context", self._log_type.value)

    def _update(self, **kwargs):
        self._log_system._update_current_entry(**kwargs)
        
        
class Handler(ABC):
    @abstractmethod
    def handle(self, log: LogEvent):
        pass

    @property
    @abstractmethod
    def is_realtime(self) -> bool:
        pass

class RealTimeHandler(Handler):
    @property
    def is_realtime(self) -> bool:
        return True

class NonRealTimeHandler(Handler):
    @property
    def is_realtime(self) -> bool:
        return False
    
class LLMRobotPlannerLogSystem():

    _instance = None  # singleton
    _handlers: List[Handler] = []
    _log_stack: List[LogRecord] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMRobotPlannerLogSystem, cls).__new__(cls)
        return cls._instance
    

    def add_handler(self, handler: Handler):
        self._handlers.append(handler)
    
    def remove_handler(self, handler: Handler):
        self._handlers.remove(handler)
    
    def event(
        self, 
        name: str, 
        context: Optional[str] = None,
        tag: Union[FrozenSet[str], Set[str]] = frozenset(),
        metadata: Dict[str, MetadataValueType] = {}
    ) -> uuidv4_str:
        return self._log_instant_entry(
            log_type=LogType.EVENT,
            name=name,
            context=context,
            tag=tag,
            metadata=metadata
        )
    
    @contextmanager
    def trace(
        self,
        name: str,
        tag: Union[FrozenSet[str], Set[str]] = frozenset(),
        metadata: Dict[str, MetadataValueType] = {}
    ):
        uid = self._begin_log_entry(LogType.TRACE, name, tag, metadata)
        context = LogEntryContext(self, uid, LogType.TRACE)
        try:
            yield context
        except Exception as e:
            # TODO: Errorのログの記録方法を変える
            self._update_current_entry(feedback=str(e))
            self._end_log_entry()
            raise e
        finally:
            self._end_log_entry()
    
    @contextmanager
    def action(
        self,
        name: str,
        tag: Union[FrozenSet[str], Set[str]] = frozenset(),
        metadata: Dict[str, MetadataValueType] = {}
    ):
        uid = self._begin_log_entry(LogType.ACTION, name, tag, metadata)
        context = LogEntryContext(self, uid, LogType.ACTION)
        try:
            yield context
        except Exception as e:
            # TODO: Errorのログの記録方法を変える
            self._update_current_entry(feedback=str(e))
            self._end_log_entry()
            raise e
        finally:
            self._end_log_entry()
    
    @contextmanager
    def span(
        self,
        name: str,
        tag: Union[FrozenSet[str], Set[str]] = frozenset(),
        metadata: Dict[str, MetadataValueType] = {}
    ):
        uid = self._begin_log_entry(LogType.SPAN, name, tag, metadata)
        context = LogEntryContext(self, uid, LogType.SPAN)
        try:
            yield context
        except Exception as e:
            # TODO: Errorのログの記録方法を変える
            self._update_current_entry(feedback=str(e))
            self._end_log_entry()
            raise e
        finally:
            self._end_log_entry()
    
    
    def _begin_log_entry(self, log_type: LogType, *args, **kwargs):
        parent = self._log_stack[-1].uid if self._log_stack else None
        
        record = self._create_record(log_type, *args, **kwargs, parent=parent)
        if self._log_stack:
            self._log_stack[-1] = self._log_stack[-1].with_child(record.uid)
        self._log_stack.append(record)
        event = LogEvent(LogEventType.BEGIN, record)
        self._process_handler(event, realtime=True)
        return record.uid
    
    def _end_log_entry(self, uid=None):        
        if uid is None:
            record = self._log_stack.pop(-1)
            if isinstance(record, DurationLogRecord):
                updated_record = record.with_end_time()
                event = LogEvent(LogEventType.END, updated_record, record, {"end_time": updated_record.end_time})
            else:
                event = LogEvent(LogEventType.END, record)
            self._process_handler(event)
        else:
            for i, record in enumerate(reversed(self._log_stack)):
                if record.uid == uid:
                    index = len(self._log_stack) - i - 1
                    break
            else:
                return
            while len(self._log_stack) > index:
                record = self._log_stack.pop(-1)
                if isinstance(record, DurationLogRecord):
                    updated_record = record.with_end_time()
                    event = LogEvent(LogEventType.END, updated_record, record, {"end_time": updated_record.end_time})
                else:
                    event = LogEvent(LogEventType.END, record)
                self._process_handler(event)
            
    def _update_current_entry(self, **kwargs):
        if self._log_stack:
            previous_record = self._log_stack[-1]
            updated_record = previous_record.create_new(**kwargs)
            self._log_stack[-1] = updated_record
            event = LogEvent(LogEventType.UPDATE, updated_record, previous_record, kwargs)
            self._process_handler(event, realtime=True)
                    
    def _log_instant_entry(self, log_type: LogType, *args, **kwargs) -> uuidv4_str:
        parent = self._log_stack[-1].uid if self._log_stack else None
        record = self._create_record(log_type, *args, **kwargs, parent=parent)
        log_event = LogEvent(LogEventType.END, record)
        self._process_handler(log_event)
        return record.uid
    
    def _create_record(self, log_type: LogType, *args, **kwargs) -> LogRecord:
        if log_type == LogType.TRACE:
            return Trace(*args, **kwargs)
        elif log_type == LogType.ACTION:
            return Action(*args, **kwargs)
        elif log_type == LogType.SPAN:
            return Span(*args, **kwargs)
        elif log_type == LogType.EVENT:
            return Event(*args, **kwargs)
        else:
            raise ValueError(f"Unknown log type: {log_type}")
        
    def _process_handler(self, event: LogEvent, realtime: bool = False):
        for handler in self._handlers:
            if realtime and handler.is_realtime:
                handler.handle(event)
            elif not realtime:
                handler.handle(event)
