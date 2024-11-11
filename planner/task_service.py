from typing import List, Union, Dict
from planner.llm.gen_ai import UnifiedAIRequestHandler as LLM
from planner.llm.parser import JsonParser
from planner.database.database import DatabaseManager
from prompts.utils import get_prompt

from planner.database.data_type import TaskRecord, CommandRecord

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
                status="pending",
                is_active=True
            ) for i, task in enumerate(response["tasks"].values())
        ]
        
    def generate_command_calls(
        self, 
        task_description: str, 
        task_additional_info: str,
        cmd_disc_list: List[str],
        action_history: str,
        knowledge: List[str]
    ) -> List[CommandRecord]:
        """
        タスクから、そのタスクを実行する為のコマンド（行動）のリストを生成する
        
        Args:
            task_description (str): タスクの内容
            task_detail (str): タスクの詳細
            cmd_disc_list (List[str]): コマンドの説明のリスト
            action_history (str): アクション履歴
            knowledge (List[str]): 知識のリスト
        
        Returns:
            List[CommandRecord]: コマンドのリスト
        """
        # コマンド一覧の生成
        command_description = "\n".join(f"        {idx}: {action}" for idx, action in enumerate(cmd_disc_list, 1))
        
        # 知識一覧の生成
        k = "\n".join([f'       ・{s}' for s in knowledge]) if knowledge else "       取得した情報はありません"
        
        # プロンプトの取得と生成
        prompt = get_prompt(
            prompt_name="generate_commands_from_task",
            replacements={
                "task_description": task_description,
                "task_detail": task_additional_info,
                "command_description": command_description,
                "action_history": action_history,
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
                status="pending",
                is_active=True
            ) for i, d in enumerate(response.values())
        ]
            

    def regenerate_command_calls(self, task_description: str, task_detail: str, cmd_disc_list: List[str], action_history: str, knowledge: List[str]) -> dict:
        # コマンド一覧の生成
        command_description = "\n".join(f"        {idx}: {action}" for idx, action in enumerate(cmd_disc_list, 1))
        
        # 知識一覧の生成
        k = "\n".join([f'       ・{s}' for s in knowledge]) if knowledge else "       取得した情報はありません"
        
        # プロンプトの取得と生成
        prompt = get_prompt(
            prompt_name="generate_commands_from_task",
            replacements={
                "task_description": task_description,
                "task_detail": task_detail,
                "command_description": command_description,
                "action_history": action_history,
                "knowledge": k, 
                "location_info": str(self._get_all_location_knowledge_names())
            },
            symbol=("{{", "}}")
        )

        # 生成
        response = self._json_parser.parse(
            text=self._llm.generate_content(
                prompt=prompt, 
                model_name=None
            ),
            response_type="json",
            convert_type="dict"
        )
        return response
    
        
    