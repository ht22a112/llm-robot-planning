from typing import List, Union, Dict
from planner.llm.gen_ai import UnifiedAIRequestHandler as LLM
from prompts.utils import get_prompt

from planner.database.database import Task # TODO: 後に削除

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class TaskService():
    def __init__(self, llm: LLM):
        self.llm = llm
    
    # 後で削除
    def _get_all_knowledge_names(self) -> List[str]:
        return ["オブジェクト（物、物体）の位置", "場所の位置情報", "周囲に居る人の性別および名前に関する情報", "自身の過去の行動に関する情報"]
    
    def split_task(self, task_description: str, task_detail: str, cmd_disc_list: List[str], action_history: str) -> dict:
        
        # コマンド一覧の生成
        command_discription = cmd_disc_list
        result = ""
        for idx, content in enumerate(command_discription, 1):
            if idx == 1:
                result += f"{idx}: {content}\n"
            else:
                result += f"    {idx}: {content}\n"
        command_discription = result
        
        prompt = get_prompt(
            prompt_name="split_task",
            replacements={
                "task_description": task_description,
                "task_detail": task_detail,
                "command_discription": command_discription,
                "action_history": action_history
            },
            symbol=("{{", "}}")
        )
        
        response = self.llm.generate_content_v2(
            prompt=prompt, 
            response_type="json", 
            convert_type="dict",
            model_name=None
        )
        return response
        
        
        
    def split_instruction(self, instruction: str) -> List[Task]:
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            List[Task]: ロボットに与える命令のリスト
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
        
        response = self.llm.generate_content_v2(
            prompt=prompt,
            response_type="json",
            convert_type="dict",
            model_name=None
        )
            
        return [
            Task(
                description=task.get("description"), 
                detail=task.get("detail"),
                required_info=task.get("required information")
            ) for task in response["tasks"].values()
        ]