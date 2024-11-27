from planner.database.data_type import CommandExecutionResultRecord, TaskRecord, CommandRecord
from planner.database.database import DatabaseManager
from planner.llm.gen_ai import UnifiedAIRequestHandler as LLM
from planner.llm.parser import JsonParser
from prompts.utils import get_prompt
from utils.utils import to_json_str

from typing import TypedDict, Literal, Union, Dict, List

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class ReplanningData(TypedDict):
    replanning_level: Literal["task", "command"]
    cause: str
    detail: str
    solution: str
    failed_task_sequence_number: int  # エラーが発生したタスクの実行ID
    failed_command_sequence_number: int  # エラーが発生したコマンドの実行ID
    
class EvaluatorResult(TypedDict):
    is_replanning_needed: bool
    replanning_data: Dict[str, ReplanningData]
    
class ResultEvaluator:
    def __init__(self, db_manager: DatabaseManager, llm: LLM):
        self._db: DatabaseManager = db_manager
        self._llm: LLM = llm
        self._json_parser = JsonParser()
        
    def evaluate_execution_command_result(
        self,
        current_task: TaskRecord,
        current_command: CommandRecord,
    ) -> EvaluatorResult:
        
        r_data = {}
        if current_command.status == "failure":
            replanning_datas = self._generate_replanning_data(current_task, current_command)
            for i in range(len(replanning_datas)):
                r_data[f"{i+1}"] = ReplanningData(
                    replanning_level=replanning_datas[f"{i+1}"]["error_level"],
                    cause=replanning_datas[f"{i+1}"]["cause"],
                    detail=replanning_datas[f"{i+1}"]["detail"],
                    solution=replanning_datas[f"{i+1}"]["solution"],
                    failed_task_sequence_number=current_task.sequence_number,
                    failed_command_sequence_number=current_command.sequence_number
                )
            
        return EvaluatorResult(
            is_replanning_needed=(current_command.status == "failure"),
            replanning_data=r_data
        )

    def evaluate_execution_task_result(
        self,
        current_task: TaskRecord,
        current_commands: List[CommandRecord],
    ):
        """
        タスクの実行結果を意図した結果を得られているか評価する
        """
        pass
        # current_task.outcome.desired_information
        # current_task.outcome.desired_robot_state
    
    
    def _generate_replanning_data(
        self,
        current_task: TaskRecord, 
        current_command: CommandRecord
    ):
        with log.span(name="Evaluate Result") as span:
            assert isinstance(current_command.execution_result, CommandExecutionResultRecord), "current_command.execution_result は CommandExecutionResultRecord である必要があります。"
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
                        "status": current_command.status,
                        "detailed_info": current_command.execution_result.detailed_info,
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