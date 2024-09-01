from logger.logger import LogRecord
from gui.real_time_info_view import LLMRobotPlannerRealTimeInfoView
import uuid

def uuid_bytes_to_str(uuid_bytes: bytes) -> str:
    uuid_obj = uuid.UUID(bytes=uuid_bytes)
    return str(uuid_obj)
    
class LoggingGUIHandler:
    def __init__(self, gui_instance: LLMRobotPlannerRealTimeInfoView):
        self.gui = gui_instance
        
    def handle(self, log: LogRecord):
        action = log.action
        detail = log.detail if log.detail is not None else ""
        uid = uuid_bytes_to_str(log.uid)
        timestamp = str(log.timestamp)
        
        self.gui.append_list_item(
            action_text=action,
            detail_text=detail,
            timestamp_text=timestamp,
            uid_text=uid
        )
        