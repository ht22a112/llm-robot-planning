from planner.command.command_base import CommandExecutionResult
from planner.database.database import DatabaseManager

class ResultEvaluator:
    def __init__(self, db_manager: DatabaseManager):
        self._db: DatabaseManager = db_manager
    
    def evaluate(self, cmd_result: CommandExecutionResult):            
        self._db.log_robot_action(
            action=cmd_result.cmd_name,
            status=cmd_result.status,
            details=cmd_result.details,
            x=None,
            y=None,
            z=None
        )
