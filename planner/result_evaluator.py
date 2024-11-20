from planner.command.command_base import CommandExecutionResult
from planner.database.data_type import CommandExecutionResultRecord, TaskRecord, CommandRecord
from planner.database.database import DatabaseManager
from planner.llm.gen_ai import UnifiedAIRequestHandler as LLM
from planner.llm.parser import JsonParser
from prompts.utils import get_prompt
from utils.utils import to_json_str

from typing import TypedDict, Literal, Union, Dict

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class ReplanningData(TypedDict):
    replanning_level: Literal["task", "command"]
    cause: str
    detail: str
    
class EvaluatorResult(TypedDict):
    is_replanning_needed: bool
    replanning_data: Dict[str, ReplanningData]
    
class ResultEvaluator:
    def __init__(self, db_manager: DatabaseManager, llm: LLM):
        self._db: DatabaseManager = db_manager
        self._llm: LLM = llm
        self._json_parser = JsonParser()
        
    def evaluate(
        self,
        current_task: TaskRecord,
        current_command: CommandRecord,
        command_result: CommandExecutionResult,
    ) -> EvaluatorResult:
        
        r_data = {}
        if command_result.status == "failure":
            replanning_datas = self._generate_replanning_data(current_task, current_command, command_result)
            for i in range(len(replanning_datas)):
                r_data[f"{i+1}"] = ReplanningData(
                    replanning_level=replanning_datas[f"{i+1}"]["error_level"],
                    cause=replanning_datas[f"{i+1}"]["cause"],
                    detail=replanning_datas[f"{i+1}"]["detail"]
                )
            
        return EvaluatorResult(
            is_replanning_needed=(command_result.status == "failure"),
            replanning_data=r_data
        )

    def _generate_replanning_data(
        self,
        current_task: TaskRecord, 
        current_command: CommandRecord, 
        command_result: CommandExecutionResult
    ):
        with log.span(name="Evaluate Result") as span:
            prompt = get_prompt(
                prompt_name="EVALUATE_RESULT",
                replacements={
                    "task": to_json_str({
                        "task_additional_info": current_task.additional_info,
                        "task_description": current_task.description,
                    }),
                    "command": to_json_str({
                        "command_name": current_command.description,
                        "args": current_command.args,
                    }),
                    "command_execution_result": to_json_str({
                        "status": command_result.status,
                        "detailed_info": command_result.details,
                    })
                },
                symbol=("{{", "}}")
            )
            response = self._llm.generate_content(
                prompt=prompt
            )
            r = self._json_parser.parse(
                response,
                response_type="json",
                convert_type="dict"
            )
            span.output(to_json_str(r))
        return r