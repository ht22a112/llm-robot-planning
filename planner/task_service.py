from typing import List, Union, Dict
from planner.llm.gen_ai import UnifiedAIRequestHandler as LLM
from planner.llm.parser import JsonParser
from planner.database.database import DatabaseManager
from prompts.utils import get_prompt
from utils.utils import to_json_str

from planner.database.data_type import TaskRecord, CommandRecord
from planner.result_evaluator import ReplanningData

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
    
    def interpret_instruction(self, instruction: str) -> List[TaskRecord]:
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            List[TaskRecord]: タスクのリスト
        """
        
        obtainable_information_list = "".join(f'・{name}\n' for name in self._get_all_knowledge_names())
        prompt = get_prompt(
            prompt_name="interpret_instruction",
            replacements={
                "obtainable_information_list": str(obtainable_information_list),
                "instruction": instruction,
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
        
        #TODO: ここでresponseの内容と形式が合っているか確認する処理の追加
        
        return [
            TaskRecord(
                sequence_number=i,
                description=task.get("description"), 
                additional_info=task.get("detail"),
                status="pending"
            ) for i, task in enumerate(response["tasks"].values())
        ]
    
    def reinterprete_instruction(
        self, 
        instruction: str, 
        replanning_data: ReplanningData
    ) -> List[TaskRecord]:
        
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            List[TaskRecord]: タスクのリスト
        """
        
        obtainable_information_list = "".join(f'・{name}\n' for name in self._get_all_knowledge_names())
        prompt = get_prompt(
            prompt_name="reinterpret_instruction",
            replacements={
                "obtainable_information_list": str(obtainable_information_list),
                "instruction": instruction,
                "cause": replanning_data["cause"],
                "cause_detail": replanning_data["detail"]
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
        
        #TODO: ここでresponseの内容と形式が合っているか確認する処理の追加
        
        return [
            TaskRecord(
                sequence_number=i,
                description=task.get("description"), 
                additional_info=task.get("detail"),
                status="pending"
            ) for i, task in enumerate(response["tasks"].values())
        ]
        
        
        
        
    def generate_command_calls(
        self, 
        task: TaskRecord,
        command_description_list: List[str],
        command_history: List[CommandRecord],
        knowledge: List[str]
    ) -> List[CommandRecord]:
        """
        タスクから、そのタスクを実行する為のコマンド（行動）のリストを生成する
        
        Args:
            task_description (str): タスクの内容
            task_detail (str): タスクの詳細
            command_description_list (List[str]): コマンドの説明のリスト
            command_history (str): アクション履歴
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
            CommandRecord(
                sequence_number=i,
                description=d["name"],
                additional_info="",
                args=d["args"],
                status="pending"
            ) for i, d in enumerate(response.values())
        ]
            

    def regenerate_command_calls(
        self, 
        task: TaskRecord, 
        replanning_data: ReplanningData,
        command_description_list: List[str],
        command_history: List[CommandRecord],
        knowledge: List[str]
    ) -> List[CommandRecord]:
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
            CommandRecord(
                sequence_number=i,
                description=d["name"],
                additional_info="",
                args=d["args"],
                status="pending"
            ) for i, d in enumerate(response.values())
        ]
            

    
        
    