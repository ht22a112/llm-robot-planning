from typing import List, Union, Dict
import json

import logging
logger = logging.getLogger("LLMRobotPlanner")

from llm.gen_ai import UnifiedAIRequestHandler

from llm.command_base import CommandBase, CommandExecutionResult

from knowledge.database import DatabaseManager, Task
from knowledge.message import *



class LLMRobotPlanner():
    def __init__(self, api_keys: dict, commands: List[CommandBase]):
        self.chat_ai = UnifiedAIRequestHandler(
            api_keys=api_keys
        )
        self._commands: Dict[str, CommandBase] = {}
        self.db: DatabaseManager = DatabaseManager() 

        self.register_command(commands)
    
    def register_command(self, commands: List[CommandBase]):
        for command in commands:
            if not isinstance(command, CommandBase):
                raise TypeError("command must be subclass of CommandBase")
            
            command_name = command.get_name()
            if command_name in self._commands:
                raise ValueError(f"command: '{command_name}' is already registered. command name must be unique")
            self._commands[command_name] = command
            
    def _get_all_command_discriptions(self) -> List[str]:
        return [command.get_command_discription() for command in self._commands.values()]
    
    def _get_command(self, name) -> CommandBase:
        # TODO: 追加の処理を追加する
        return self._commands[name]
        
    def initialize(self, instruction: str):
        """
        初期化
        
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        
        Returns:
            tasks: List[Task]
        """
        
        tasks = self.split_instruction(instruction)
        
        logger.info(
            f"[*]initialize >> create new job\n"
            f"[-]instruction: {instruction}\n"
            f"[-]tasks: {tasks}\n"
        )
        
        self.db.start_new_job(
            instruction=instruction,
            tasks=tasks
        )
        
        return tasks
        

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
        
        # tasksの実行
        for task in tasks:
            # taskの分解
            functions = self.get_call_func_dict(task.description)
            task.func_dict = functions
            # taskの分解結果の表示
            for commandN, command in functions.items():
                func_name = command["name"]
                func_args = command["args"]
                logger.info(f"task: {task.description}\n"
                            f"required_info: {task.required_info}\n"
                            f"{commandN}> {func_name}: {func_args}")
            
            # commandの実行
            for commandN, command in functions.items():
                func_name = command["name"]
                func_args = command["args"]
                logger.info(f"[EXEC] {commandN}: {func_name}")
                exec_result = self.execute_command(func_name, func_args)
                logger.info(f"[RESULT] {exec_result}")
                
            yield functions
    
    
    def execute_command(self, command_name: str, args: dict) -> CommandExecutionResult:
        """
        コマンドを実行する
        
        Args:
            command_name: 実行するコマンド名
            args: dict[str, Any] 
                {
                    "arg1_name": "value",
                    "arg2_name": "value"
                }
            
        Returns:
            CommandExecutionResult
        """
        return self._get_command(command_name).execute()
        
    
    def get_call_func_dict(self, task_description: str) -> dict:
        command_discription = self._get_all_command_discriptions()

        result = ""
        for idx, content in enumerate(command_discription, 1):
            if idx == 1:
                result += f"{idx}: {content}\n"
            else:
                result += f"            {idx}: {content}\n"
        command_discription = result
        
        # TODO: 後で実装方法変える
        system_prompt = f"""
        [role] あなたは自立思考型ロボットの行動決定システムです。
        今から与える指示を以下の例のようにロボットが実行可能なコマンドに分割してください。
        複数に分割する必要がない場合は、分割する必要はありません。
        <分割する指示>
            「{task_description}」
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
            {command_discription}
            
        制約：
            1. JSON形式でのみ回答してください!!
            2. 二重引用符で囲まれたコマンド名のみを使用してください。例： "コマンド名"
            3. ここに書かれていないコマンドは絶対に実行できません。適切なコマンドが見つからない場合は、コマンド"error"でargsのmessageにエラー内容を記述して出力してください

        パフォーマンス評価：
            自分の能力を最大限に発揮できるように、行動を継続的に見直し、分析してください。
            大局的な行動について、建設的な自己批判を常に行ってください。
            過去の決定や戦略を振り返り、アプローチを洗練させてください。
            すべてのコマンドにはコストがかかるので、賢明で効率的に行動してください。できるだけ少ないステップでタスクを完了することを目指してください。
            以下のようなJSON形式でのみ回答してください

        <<必ず以下の回答のフォーマットに従って回答してください>>
        回答フォーマット：
            {{
                "command1": {{
                    "name": "command_name",
                    "args":{{
                        "arg1_name": "value",
                        "ag2_name": "value"
                    }}
                }},
                "command2": {{
                    "name": "command_name",
                    "args":{{
                        "arg1_name": "value",
                        "arg2_name": "value"
                    }}
                }}
                etc...
            }}

        必ず結果は必ず"json形式"で生成してください!!
        """
        
        response = self.chat_ai.generate_content(system_prompt)
        logger.debug(response)
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
        [role] あなたは自立思考型ロボットの行動決定システムです。
        今から与える指示が複数のタスクに分かれている場合は以下の例のように分割してください。
        ・与えられた指示について「何をどうするのか」と複数のタスクに分割してください
        ・複数のタスクに分かれていない場合は、そのままロボットに与える命令を返してください!!
        ・複数のタスクに分割を行う場合、元の指示から分割後に情報が失われないように気を付けて分割してください！！
        ・タスクの実行を行う際に必要な情報であると考えられる情報が、以下の取得できる情報一覧の中にある場合はその取得が必要な項目についても項目名をそのまま記述してください （例:「りんごを取る」というタスクの実行にはりんごの位置情報が必要であると考えられる、そしてその場合に<取得できる情報一覧>にオブジェクトの位置情報とある場合は "required information": ["オブジェクトの位置情報"] と出力する。他にもキッチンに移動するというタスクを行う場合はキッチンの位置情報が必要であると考えられ、<取得できる情報一覧>に場所の位置情報という情報が入っている場合は "required information": ["場所の位置情報"] と出力する。）
        ・必ず元の位置や現在位置に戻る必要があるか考えてください。必要であれば"元の位置"や"現在位置"に戻ってください！！
        ・必ず回答や返事を返す必要があるか考えてください。必要であれば回答や返事を返すようにタスクを構築してください！！

        <取得できる情報一覧>
        ・オブジェクトの位置情報
        ・場所の位置情報
        ・周囲に居る人の性別および名前に関する情報
        ・自身の過去の行動に関する情報

        <指示>
        「{instruction}」

        <文章の分割例>
        元の文章: 「あなたは何ができますか？、また机の上にある本を取ってきて」
        分割後の文章: "自身について説明する", "机に移動する", "本を取る", "元の位置に戻る", 

        <レスポンスの形式(json)>
        {{
            "tasks": {{  
                "task1": {{
                    "description": "content",  # タスクの内容
                    "detail": "content",  # タスクの詳細
                    "required information":["content1", "content2", etc...]  # タスクの実行に必要な情報
                }},
                "task2": {{
                    "description": "content",  # タスクの内容
                    "detail": "content",  # タスクの詳細
                    "required information":["content1", "content2", etc...]  # タスクの実行に必要な情報
                }},
                etc...
            }}
        }}

        必ず結果は必ずjson形式で生成してください!!
        """

        response = self.chat_ai.generate_content(system_prompt)
        logger.debug(response)
        try:
            response_py_obj = json.loads(response)
        except json.JSONDecodeError as e:
            from utils.json import fix_and_parse_json
            response_py_obj = fix_and_parse_json(response)
            
        if not isinstance (response_py_obj, dict):
            raise ValueError(f"json format error: {response_py_obj}")
            
        return [
            Task(
                task.get("description"), 
                task.get("required information")
            ) for task in response_py_obj["tasks"].values()
        ]