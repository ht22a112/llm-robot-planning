class LogRecordError(Exception):
    """LogRecordに関連するエラーの基底クラス"""
    pass

class InvalidTypeError(LogRecordError):
    """無効な型が使用された場合のエラー"""
    pass

class LogEntryError(Exception):
    """Base class for exceptions in the LogEntryContext."""
    pass

class InvalidLogOperationError(LogEntryError):
    """Exception raised for invalid operations on a log entry."""
    def __init__(self, operation: str, log_type: str):
        self.operation = operation
        self.log_type = log_type
        self.message = f"Invalid operation '{operation}' for log type '{log_type}'"
        super().__init__(self.message)