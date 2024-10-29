from typing import List, Union, Dict
from planner.llm.gen_ai import UnifiedAIRequestHandler as LLM
from planner.llm.parser import JsonParser
from planner.database.database import DatabaseManager
from prompts.utils import get_prompt

from planner.database.data_type import TaskRecord # TODO: 後に削除

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
        
    def split_task(self, task_description: str, task_detail: str, cmd_disc_list: List[str], action_history: str, knowledge: List[str]) -> dict:
        
        # コマンド一覧の生成
        command_discription = "\n".join(f"        {idx}: {content}" for idx, content in enumerate(cmd_disc_list, 1))
        
        # 知識一覧の生成
        k = "\n".join([f'       ・{s}' for s in knowledge])
        
        # プロンプトの取得と生成
        prompt = get_prompt(
            prompt_name="split_task",
            replacements={
                "task_description": task_description,
                "task_detail": task_detail,
                "command_discription": command_discription,
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
        

    def split_instruction(self, instruction: str) -> List[TaskRecord]:
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            List[TaskRecord]: ロボットに与える命令のリスト
        """
        
        obtainable_information_list = "".join(f'・{name}\n' for name in self._get_all_knowledge_names())
        prompt = get_prompt(
            prompt_name="split_instruction",
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
            
        return [
            TaskRecord(
                description=task.get("description"), 
                detail=task.get("detail"),
                required_info=task.get("required information")
            ) for task in response["tasks"].values()
        ]