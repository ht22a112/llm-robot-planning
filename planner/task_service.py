from typing import List, Union, Dict
from planner.llm.gen_ai import UnifiedAIRequestHandler as LLM
from planner.llm.parser import JsonParser
from planner.database.database import DatabaseManager
from prompts.utils import get_prompt
from utils.utils import to_json_str

from planner.database.data_type import (
    TaskInfo, CommandInfo,
    TaskRecord, CommandRecord,
    DesiredInformation, DesiredRobotState, 
    Dependencies, EnvironmentalConditions, InformationConditions, TaskOutcome
)
from planner.result_evaluator import ReplanningData
from planner.command.robot_state import RobotState

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class TaskService():
    def __init__(self, llm: LLM, db: DatabaseManager):
        self._llm: LLM = llm
        self._json_parser = JsonParser()
        self._db = db
        
    # 後で削除
    def _get_all_knowledge_names(self) -> List[str]:
        return ["オブジェクト（物、物体）の位置", "場所の位置情報", "周囲に居る人の性別および名前に関する情報", "自身の過去の行動に関する情報"]
    
    def _get_all_location_knowledge_names(self) -> List[str]:
        return list(set([location.name for location in self._db.get_all_known_locations()]))

    def generate_tasks(self, instruction: str, states: List[RobotState]) -> List[TaskInfo]:
        state_descriptions = ""
        for state in states:
            arg = ", ".join((f"{k}: {v}" if v else k for k, v in state.args_description.items()))
            state_descriptions += f"- {state.name}({arg}): {state.description}\n"

        prompt = get_prompt(
            prompt_name="GENERATE_TASKS",
            replacements={
                "instruction": instruction,
                "state_descriptions": state_descriptions,
            },
            symbol=("{{", "}}")
        )
        
        response = self._json_parser.parse(
            text=self._llm.generate_content(
                prompt=prompt, 
                model_name=None
            ),
            response_type="json",
            convert_type="dict"
        )
        
        # TODO: ここでresponseの内容と形式が合っているか確認する処理の追加
        # TODO: taskの依存関係を解析する処理の追加
        return [
            TaskInfo(
                sequence_number=i,
                description=task["task_description"], 
                additional_info=task.get("task_additional_info") if task.get("task_additional_info") is not None else "",
                dependencies=tuple(
                    Dependencies(
                        dependency_sequence_number=dep["dependency_task_sequence_number"],
                        reason=dep["reason"],
                        required_outcome_desired_robot_state_uids=dep.get("required_outcome_desired_robot_state_uids", []),
                        required_outcome_desired_information_uids=dep.get("required_outcome_desired_information_uids", []),
                    ) for dep in task.get("task_dependencies", [])
                ),
                environmental_conditions=EnvironmentalConditions(
                    physical=task.get("task_environmental_conditions", {}).get("required_physical_conditions", []),
                    information=InformationConditions(
                        locations=task.get("task_environmental_conditions", {}).get("required_information_conditions", {}).get("required_information_locations", []),
                        objects=task.get("task_environmental_conditions", {}).get("required_information_conditions", {}).get("required_information_objects", [])
                    ),
                ),      
                reason=task["task_reason"],
                outcome=TaskOutcome(
                    desired_information=tuple(
                        DesiredInformation(
                            uid=info["uid"],
                            description=info["description"]
                        ) for info in task.get("task_outcome", []).get("desired_information", [])
                    ),
                    desired_robot_state=tuple(
                        DesiredRobotState(
                            uid=state["uid"],
                            name=state["state_name"],
                            args=state.get("arg", [])
                        ) for state in task.get("task_outcome", []).get("desired_robot_state", [])
                    ) 
                )
            ) for i, task in enumerate(response["tasks"], 1)
        ]
        
        
    def regenerate_tasks(
        self, 
        instruction: str, 
        states: List[RobotState],
        executed_tasks: List[TaskRecord],
        replanning_data: ReplanningData
    ) -> List[TaskInfo]:
        
        # --プロンプトに含めるデータの加工--
        # state
        state_descriptions = ""
        for state in states:
            arg = ", ".join((f"{k}: {v}" if v else k for k, v in state.args_description.items()))
            state_descriptions += f"- {state.name}({arg}): {state.description}\n"
        # tasks
        formatted_execution_tasks = {"tasks": []}
        for task in executed_tasks:
            formatted_execution_tasks["tasks"].append(
                {
                    "task_sequence_number": task.sequence_number,
                    "task_description": task.description,
                    "task_additional_info": task.additional_info,
                    "task_dependencies": [
                        {
                            "dependency_task_sequence_number": dependencie.dependency_sequence_number,
                            "reason": dependencie.reason,
                            "required_outcome_desired_information_uids": dependencie.required_outcome_desired_information_uids,
                            "required_outcome_desired_robot_state_uids": dependencie.required_outcome_desired_robot_state_uids
                        } for dependencie in task.dependencies
                    ],
                    "task_environmental_conditions": {
                        "required_physical_conditions": task.environmental_conditions.physical,
                        "required_information_conditions": {
                            "required_information_locations": task.environmental_conditions.information.locations,
                            "required_information_objects": task.environmental_conditions.information.objects
                        }
                    },
                    "task_reason": task.reason,
                    "task_outcome": {
                        "desired_information": [
                            {
                                "uid": desired_information.uid,
                                "description": desired_information.description
                            } for desired_information in task.outcome.desired_information
                        ],
                        "desired_robot_state": [
                            {
                                "uid": desired_robot_state.uid,
                                "state_name": desired_robot_state.name,
                                "state_args": [arg for arg in desired_robot_state.args]
                            } for desired_robot_state in task.outcome.desired_robot_state
                        ]
                    }
                }
            )
        
        # promptの取得とreplace 
        prompt = get_prompt(
            prompt_name="REGENERATE_TASKS",
            replacements={
                "instruction": instruction,
                "state_descriptions": state_descriptions,
                "execution_tasks": to_json_str(formatted_execution_tasks, indent=2),
                "failed_task_solution": replanning_data["solution"],
                "failed_task_id": str(replanning_data["failed_task_sequence_number"]),
                "next_failed_task_id": str(replanning_data["failed_task_sequence_number"] + 1),
                "failed_cause": replanning_data["cause"],
                #
                "cause_detail": replanning_data["detail"]
                
            },
            symbol=("{{", "}}")
        )
        
        # LLM生成と結果をDict形式に変換
        response = self._json_parser.parse(
            text=self._llm.generate_content(
                prompt=prompt, 
                model_name=None
            ),
            response_type="json",
            convert_type="dict"
        )
        
        # TODO: ここでresponseの内容と形式が合っているか確認する処理の追加
        # TODO: taskの依存関係を解析する処理の追加
        return [
            TaskInfo(
                sequence_number=i,
                description=task["task_description"], 
                additional_info=task.get("task_additional_info") if task.get("task_additional_info") is not None else "",
                dependencies=tuple(
                    Dependencies(
                        dependency_sequence_number=dep["dependency_task_sequence_number"],
                        reason=dep["reason"],
                        required_outcome_desired_robot_state_uids=dep.get("required_outcome_desired_robot_state_uids", []),
                        required_outcome_desired_information_uids=dep.get("required_outcome_desired_information_uids", []),
                    ) for dep in task.get("task_dependencies", [])
                ),
                environmental_conditions=EnvironmentalConditions(
                    physical=task.get("task_environmental_conditions", {}).get("required_physical_conditions", []),
                    information=InformationConditions(
                        locations=task.get("task_environmental_conditions", {}).get("required_information_conditions", {}).get("required_information_locations", []),
                        objects=task.get("task_environmental_conditions", {}).get("required_information_conditions", {}).get("required_information_objects", [])
                    ),
                ),      
                reason=task["task_reason"],
                outcome=TaskOutcome(
                    desired_information=tuple(
                        DesiredInformation(
                            uid=info["uid"],
                            description=info["description"]
                        ) for info in task.get("task_outcome", []).get("desired_information", [])
                    ),
                    desired_robot_state=tuple(
                        DesiredRobotState(
                            uid=state["uid"],
                            name=state["state_name"],
                            args=state.get("arg", [])
                        ) for state in task.get("task_outcome", []).get("desired_robot_state", [])
                    )
                )
            ) for i, task in enumerate(response["tasks"], 1)
        ]
        
        
    def generate_command_calls(
        self, 
        task: TaskRecord,
        command_description_list: List[str],
        command_history: List[CommandRecord],
        knowledge: List[str]
    ) -> List[CommandInfo]:
        """
        タスクから、そのタスクを実行する為のコマンド（行動）のリストを生成する
        
        Args:
            task_description (str): タスクの内容
            task_detail (str): タスクの詳細
            command_description_list (List[str]): コマンドの説明のリスト
            command_history (List[CommandRecord]): アクション履歴
            knowledge (List[str]): 知識のリスト
        
        Returns:
            List[CommandRecord]: コマンドのリスト
        """
        # TODO: データレコードを受け取るようにして、この関数内でデータの加工を行うように変更する
        # コマンド一覧の生成
        command_description = "\n".join(f"        {idx}: {action}" for idx, action in enumerate(command_description_list, 1))
        
        # 知識一覧の生成
        k = "\n".join([f'       ・{s}' for s in knowledge]) if knowledge else "       取得した情報はありません"
        
        # 行動履歴の生成
        action_history_json = "\n".join(" "*8 + line for line in to_json_str(command_history).splitlines())
        
        # プロンプトの取得と生成
        prompt = get_prompt(
            prompt_name="generate_commands_from_task",
            replacements={
                "task_description": task.description,
                "task_detail": task.additional_info,
                "command_description": command_description,
                "action_history": action_history_json,
                "knowledge": k, 
                "location_info": str(self._get_all_location_knowledge_names())
            },
            symbol=("{{", "}}")
        )

        # 生成
        # response = {
        #   "commandN": {
        #       "name": "command_name",
        #       "args": {
        #           "arg1_name": "value1",
        #           "arg2_name": "value2",
        # } 
        response = self._json_parser.parse(
            text=self._llm.generate_content(
                prompt=prompt, 
                model_name=None
            ),
            response_type="json",
            convert_type="dict"
        )
        
        return [
            CommandInfo(
                sequence_number=i,
                description=d["name"],
                additional_info="",
                args=d["args"]
            ) for i, d in enumerate(response.values())
        ]
            

    def regenerate_command_calls(
        self, 
        task: TaskRecord, 
        replanning_data: ReplanningData,
        command_description_list: List[str],
        command_history: List[CommandRecord],
        knowledge: List[str]
    ) -> List[CommandInfo]:
        """
        タスクから、そのタスクを実行する為のコマンド（行動）のリストを生成する
        
        Args:
            task_description str: タスクの内容
            task_detail str: タスクの詳細
            command_description_list List[str]: コマンドの説明のリスト
            command_history List[CommandRecord]: アクション履歴
            knowledge List[str]: 知識のリスト
        
        Returns:
            List[CommandRecord]: コマンドのリスト
        """
        # TODO: データレコードを受け取るようにして、この関数内でデータの加工を行うように変更する
        # コマンド一覧の生成
        command_description = "\n".join(f"        {idx}: {action}" for idx, action in enumerate(command_description_list, 1))
        
        # 知識一覧の生成
        k = "\n".join([f'       ・{s}' for s in knowledge]) if knowledge else "       取得した情報はありません"
        
        # 行動履歴の生成
        action_history_json = "\n".join(" "*8 + line for line in to_json_str(command_history).splitlines())
       
        # プロンプトの取得と生成
        prompt = get_prompt(
            prompt_name="REGENERATE_COMMANDS_FROM_TASK",
            replacements={
                "task_description": task.description,
                "task_detail": task.additional_info,
                "task_cause": replanning_data["cause"],
                "task_cause_detail": replanning_data["detail"],
                "command_description": command_description,
                "action_history": action_history_json,
                "knowledge": k, 
                "location_info": str(self._get_all_location_knowledge_names())
            },
            symbol=("{{", "}}")
        )

        # 生成
        # response = {
        #   "commandN": {
        #       "name": "command_name",
        #       "args": {
        #           "arg1_name": "value1",
        #           "arg2_name": "value2",
        # } 
        response = self._json_parser.parse(
            text=self._llm.generate_content(
                prompt=prompt, 
                model_name=None
            ),
            response_type="json",
            convert_type="dict"
        )
        
        return [
            CommandInfo(
                sequence_number=i,
                description=d["name"],
                additional_info="",
                args=d["args"]
            ) for i, d in enumerate(response.values())
        ]
            

    
        
    