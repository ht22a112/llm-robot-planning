from logger.logger import LogRecord, LoggerHandler
from gui.real_time_info_view import LLMRobotPlannerRealTimeInfoView
import uuid
import datetime 
def uuid_bytes_to_str(uuid_bytes: bytes) -> str:
    uuid_obj = uuid.UUID(bytes=uuid_bytes)
    return str(uuid_obj)
    
class LoggingGUIHandler(LoggerHandler):
    def __init__(self, gui_instance: LLMRobotPlannerRealTimeInfoView):
        self.gui = gui_instance
        
    def handle(self, log: LogRecord):
        action = log.action
        detail = log.detail if log.detail is not None else ""
        uid = uuid_bytes_to_str(log.uid)
        #timestamp = str(log.timestamp)
        
        # 簡易実装 後で変更する
        timestamp = float(log.timestamp)
        datetime_object = datetime.datetime.fromtimestamp(timestamp)
        formatted_datetime = datetime_object.strftime("%Y-%m-%d %H:%M:%S")
        
        self.gui.append_list_item(
            action_text=action,
            detail_text=detail,
            timestamp_text=formatted_datetime,
            uid_text=uid
        )
        