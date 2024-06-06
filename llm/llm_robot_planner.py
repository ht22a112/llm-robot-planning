from typing import List
import json
import logging

from llm.gen_ai import UnifiedAIRequestHandler

from knowledge.database import DatabaseManager, Task
from knowledge.message import *

from utils.utils import read_key_value_pairs

class LLMRobotPlanner():
    def __init__(self):
        self.chat_ai = UnifiedAIRequestHandler(
            # API Keyの設定
            api_keys={ 
                "google": read_key_value_pairs("key.env")["GEMINI_API_KEY"],
            }
        )
        self.db: DatabaseManager = DatabaseManager() 
        
    def initialize(self, instruction: str):
        """
        初期化
        
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            None
        """
        self.db.new_job(
            instruction=instruction,
            tasks=self.split_instruction(instruction)
        )
        

    def process(self):
        """
        ロボットに与える命令を処理
        
        Args:
            None
        
        Returns:
            None
        """
        if self.db.current_job is None:
            return 
        instruction = self.db.current_job.instruction
        tasks = self.db.current_job.tasks
        for task in tasks:
            functions = self.get_call_func_dict(task.content)
            for commandN, command in functions.items():
                func_name = command["name"]
                func_args = command["args"]
                print(f"[{commandN}] {func_name}: {func_args}")
                    
    
    def get_call_func_dict(self, task_content: str) -> dict:
        
        # TODO: 後で実装方法変える
        system_prompt = f"""
        あなたは自立思考型ロボットの行動決定システムです。
        今から与える指示を以下の例のようにロボットが実行可能なコマンドに分割してください。
        複数に分割する必要がない場合は、分割する必要はありません。
        <分割する指示>
            「{task_content}」
        <例>
            「机に移動する」
        <回答例>
            {{
                "command1": {{
                    "name": "move",
                    "args":{{
                        "location": "table"
                }}
            }}
        
        ロボットが実行可能なコマンド：
            1. : "move", args: "location": "<location>"  # <location>に移動するコマンド
            3. : "find", args: "object": "<object_name>"  # <object_name>をロボットのカメラを用いて見つける
            4. : "introduce_self", args: "message": "<message>"  # 自己紹介するコマンド
            5. : "error", args: "message": "<message>"  # エラーを報告するコマンド、適切な実行可能なコマンドが見つからない場合に使用する
        制約：
            1. JSON形式でのみ回答してください!!
            2. 二重引用符で囲まれたコマンド名のみを使用してください。例： "コマンド名"
            3. ここに書かれていないコマンドは絶対に実行できません。適切なコマンドが見つからない場合は、コマンド"error"を使用してエラーを報告してください
        
        パフォーマンス評価：
            自分の能力を最大限に発揮できるように、行動を継続的に見直し、分析してください。
            大局的な行動について、建設的な自己批判を常に行ってください。
            過去の決定や戦略を振り返り、アプローチを洗練させてください。
            すべてのコマンドにはコストがかかるので、賢明で効率的に行動してください。できるだけ少ないステップでタスクを完了することを目指してください。
            以下のようなJSON形式でのみ回答してください

        回答フォーマット：
            {{
                "command1": {{
                    "name": "command_name",
                    "args":{{
                        "arg1_name": "value"
                        "ag2_name": "value"
                    }}
                }},
                "command2": {{
                    "name": "command_name",
                    "args":{{
                        "arg1_name": "value"
                        "arg2_name": "value"
                    }}
                }}
                etc...
            }}

        必ず結果は必ず"json形式"で生成してください!!
        """
        
        response = self.chat_ai.generate_content(system_prompt)
        logging.debug(response)
        try:
            response_py_obj = json.loads(response)
        except json.JSONDecodeError as e:
            from utils.json import fix_and_parse_json
            response_py_obj = fix_and_parse_json(response)
            
        if not isinstance (response_py_obj, dict):
            raise ValueError(f"json format error: {response_py_obj}")
        
        return response_py_obj
        
        
        
    def split_instruction(self, instruction: str) -> List[Task]:
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            List[Task]: ロボットに与える命令のリスト
        """
        
        # TODO: 後で実装方法変える
        system_prompt = f"""
        あなたは自立思考型ロボットの行動決定システムです。
        今から与える指示が複数のタスクに分かれている場合は以下の例のように分割してください。
        複数のタスクに分かれていない場合は、そのままロボットに与える命令を返してください!!
        元の位置や現在位置に戻る必要があるか考えて、必要であれば"元の位置"や"現在位置"に戻ってください!!
        <指示>
        「{instruction}」

        <分割例>
        元の文章: 「あなたは何ができますか？、また机の上にある本を取ってきて」
        分割後: "自身について説明する", "机に移動する", "本を取る", "元の位置に戻る", 

        <レスポンスの形式(json)>
        {{
            "tasks": [
                "task1",
                "task2",
                "etc..."
            ]
        }}

        必ず結果は必ずjson形式で生成してください!!
        """

        response = self.chat_ai.generate_content(system_prompt)
        logging.debug(response)
        try:
            response_py_obj = json.loads(response)
        except json.JSONDecodeError as e:
            from utils.json import fix_and_parse_json
            response_py_obj = fix_and_parse_json(response)
            
        if not isinstance (response_py_obj, dict):
            raise ValueError(f"json format error: {response_py_obj}")

        return [Task(task) for task in response_py_obj["tasks"]]