from logger.logger import LogEvent, LogRecord, LogType, EventRecord, ActionRecord, SpanRecord, TraceRecord, LogEventType, RealTimeHandler
from gui.view.real_time_info_view import LLMRobotPlannerRealTimeInfoView 
from datetime import datetime

class LoggingGUIHandler(RealTimeHandler):
    def __init__(self, gui_instance: LLMRobotPlannerRealTimeInfoView):
        self.gui = gui_instance
        
    def handle(self, log: LogEvent):
        record: LogRecord = log.record
        if log.event_type == LogEventType.BEGIN:
            if isinstance(record, (ActionRecord, SpanRecord, TraceRecord)):
                detail_text = f"input:\n{record.input}\n\noutput:\n{record.output}\n\nfeedback:\n{record.feedback}" 
            self.gui.append_list_item(
                action_text=record.name,
                detail_text=detail_text,
                timestamp_text=datetime.fromtimestamp(record.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f'),
                uid_text=record.uid,
                is_instant=False if record.type in (LogType.ACTION, LogType.TRACE, LogType.SPAN) else True
            )
        elif log.event_type == LogEventType.UPDATE:
            if isinstance(record, (ActionRecord, SpanRecord, TraceRecord)):
                detail_text = f"input:\n{record.input}\n\noutput:\n{record.output}\n\nfeedback:\n{record.feedback}"
            else:
                raise ValueError(f"Unexpected record type: {type(record)}")
            self.gui.update_list_item(
                action_text=record.name,
                detail_text=detail_text,
                timestamp_text=datetime.fromtimestamp(record.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f'),
                uid_text=record.uid,
                is_duration_end=False
            )
        elif log.event_type == LogEventType.END:
            if isinstance(record, (ActionRecord, SpanRecord, TraceRecord)):
                detail_text = f"input:\n{record.input}\n\noutput:\n{record.output}\n\nfeedback:\n{record.feedback}"
            elif isinstance(record, EventRecord):
                detail_text = record.context
                self.gui.append_list_item(
                    action_text=record.name,
                    detail_text=detail_text,
                    timestamp_text=datetime.fromtimestamp(record.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f'),
                    uid_text=record.uid,
                    is_instant=True
                )
            else:
                raise ValueError(f"Unexpected record type: {type(record)}")
            self.gui.update_list_item(
                action_text=record.name,
                detail_text=detail_text,
                timestamp_text=datetime.fromtimestamp(record.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f'),
                uid_text=record.uid,
                is_duration_end=True if record.type in (LogType.ACTION, LogType.TRACE, LogType.SPAN) else False
            )