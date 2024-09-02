from typing import Any, Callable, Optional
import json
import uuid
import inspect
import functools
from datetime import datetime
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass(frozen=True)
class LogRecord:
    action: str
    detail: Optional[str] = None
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    uid: bytes = field(default_factory=lambda: uuid.uuid4().bytes)

    def __post_init__(self):
        if not isinstance(self.action, str):
            raise ValueError("action must be a string")
        if self.detail is not None and not isinstance(self.detail, str):
            raise ValueError("detail must be a string or None")
        if not isinstance(self.timestamp, float):
            raise ValueError("timestamp must be a float")
        if not isinstance(self.uid, bytes):
            raise ValueError("uid must be bytes")

    @classmethod
    def create(cls, action: str, detail: Optional[str] = None, 
               timestamp: Optional[float] = None, uid: Optional[bytes] = None) -> 'LogRecord':
        return cls(
            action=action,
            detail=detail,
            timestamp=timestamp if timestamp is not None else datetime.now().timestamp(),
            uid=uid if uid is not None else uuid.uuid4().bytes
        )

class LoggerHandler(ABC):
    @abstractmethod
    def handle(self, log: LogRecord):
        pass
            
class LLMRobotPlannerLogger:
    
    _instance = None  # singleton    
    _handlers = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMRobotPlannerLogger, cls).__new__(cls)
        return cls._instance
    
    def add_handler(self, handler: Any):
        self._handlers.append(handler)
    
    def remove_handler(self, handler: Any):
        self._handlers.remove(handler)
        
    def log(self, action: str, detail: Optional[str] = None):
        log = LogRecord(action, detail)
        self._process_handler(log)
    
    def _process_handler(self, log: LogRecord):
        for handler in self._handlers:
            handler.handle(log)
            
        

                
        
            
class FunctionLogger:
    @staticmethod
    def log_function(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = LLMRobotPlannerLogger()
            
            func_name = func.__name__
            signature = inspect.signature(func)
            bound_args = signature.bind(*args, **kwargs)
            args_str = json.dumps(dict(bound_args.arguments), default=str)
            logger.log(
                action="FunctionExecuted",
                detail=f"Function '{func_name}' called with arguments: {args_str}"
            )
            
            try:
                # 関数の実行
                result = func(*args, **kwargs)
                
                # 戻り値のログ
                result_str = json.dumps(result, default=str)
                logger.log(
                    action="FunctionReturned",
                    detail=f"Function '{func_name}' returned: {result_str}"
                )
                
                return result
            except Exception as e:
                # エラーのログ
                logger.log(
                    action="FunctionExceptionRaised",
                    detail=f"Function '{func_name}' raised an exception: {str(e)}"
                )
                raise
        
        return wrapper


class LoggingDataBase:
    def __init__(self):
        self.logs = []

    def add_log(self, log: LogRecord):
        self.logs.append(log)
    
    def get_logs(self):
        pass

class LoggingDatabaseHandler:
    pass
    

